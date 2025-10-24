"""
Playbook execution engine

Main orchestration logic for executing playbooks with state management.
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Callable
import logging

from ignition_toolkit.gateway import GatewayClient
from ignition_toolkit.browser import BrowserManager
from ignition_toolkit.credentials import CredentialVault
from ignition_toolkit.storage import Database, ExecutionModel, StepResultModel
from ignition_toolkit.playbook.models import (
    Playbook,
    ExecutionState,
    ExecutionStatus,
    StepResult,
    StepStatus,
    OnFailureAction,
)
from ignition_toolkit.playbook.loader import PlaybookLoader
from ignition_toolkit.playbook.parameters import ParameterResolver
from ignition_toolkit.playbook.step_executor import StepExecutor
from ignition_toolkit.playbook.state_manager import StateManager
from ignition_toolkit.playbook.exceptions import PlaybookExecutionError

logger = logging.getLogger(__name__)


class PlaybookEngine:
    """
    Execute playbooks with pause/resume/skip control

    Example:
        engine = PlaybookEngine(
            gateway_client=client,
            credential_vault=vault,
            database=db
        )

        # Execute playbook
        execution_state = await engine.execute_playbook(
            playbook,
            parameters={"gateway_url": "http://localhost:8088"}
        )

        # Control execution
        await engine.pause()
        await engine.resume()
        await engine.skip_current_step()
    """

    def __init__(
        self,
        gateway_client: Optional[GatewayClient] = None,
        credential_vault: Optional[CredentialVault] = None,
        database: Optional[Database] = None,
        state_manager: Optional[StateManager] = None,
        screenshot_callback: Optional[Callable[[str, str], None]] = None,
    ):
        """
        Initialize playbook engine

        Args:
            gateway_client: Gateway client for gateway operations
            credential_vault: Credential vault for loading credentials
            database: Database for execution tracking
            state_manager: State manager for pause/resume/skip
            screenshot_callback: Async callback for screenshot frames (execution_id, screenshot_b64)
        """
        self.gateway_client = gateway_client
        self.credential_vault = credential_vault
        self.database = database
        self.state_manager = state_manager or StateManager()
        self.screenshot_callback = screenshot_callback
        self._current_execution: Optional[ExecutionState] = None
        self._update_callback: Optional[Callable[[ExecutionState], None]] = None
        self._browser_manager: Optional[BrowserManager] = None

    def set_update_callback(self, callback: Callable[[ExecutionState], None]) -> None:
        """
        Set callback for execution updates

        Args:
            callback: Function to call on state updates
        """
        self._update_callback = callback

    async def execute_playbook(
        self,
        playbook: Playbook,
        parameters: Dict[str, Any],
        base_path: Optional[Path] = None,
        execution_id: Optional[str] = None,
    ) -> ExecutionState:
        """
        Execute playbook with parameters

        Args:
            playbook: Playbook to execute
            parameters: Parameter values
            base_path: Base path for resolving relative file paths
            execution_id: Optional execution ID (generated if not provided)

        Returns:
            Final execution state

        Raises:
            PlaybookExecutionError: If execution fails
        """
        # Create execution state FIRST (before validation)
        # This ensures ALL executions are tracked, even validation failures
        if execution_id is None:
            execution_id = str(uuid.uuid4())
        execution_state = ExecutionState(
            execution_id=execution_id,
            playbook_name=playbook.name,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(),
        )
        self._current_execution = execution_state

        # Reset state manager
        self.state_manager.reset()

        # Save to database IMMEDIATELY (before validation)
        if self.database:
            await self._save_execution_start(execution_state, playbook, parameters)

        # Initialize browser_manager to None BEFORE try block (scope issue)
        browser_manager = None

        try:
            # Validate parameters (can fail, but state already saved)
            self._validate_parameters(playbook, parameters)
            # Create parameter resolver
            resolver = ParameterResolver(
                credential_vault=self.credential_vault,
                parameters=parameters,
                variables=execution_state.variables,
            )

            # Create browser manager with screenshot streaming if callback provided
            if self.screenshot_callback:
                # Create screenshot callback that includes execution_id
                async def screenshot_frame_callback(screenshot_b64: str):
                    await self.screenshot_callback(execution_id, screenshot_b64)

                browser_manager = BrowserManager(
                    headless=True,  # Headless mode with screenshot streaming for embedded view
                    screenshot_callback=screenshot_frame_callback
                )
                await browser_manager.start()
                await browser_manager.start_screenshot_streaming()
                self._browser_manager = browser_manager  # Store reference for pause/resume
                logger.info(f"Browser screenshot streaming started for execution {execution_id}")

            # Create step executor
            executor = StepExecutor(
                gateway_client=self.gateway_client,
                browser_manager=browser_manager,
                parameter_resolver=resolver,
                base_path=base_path,
                state_manager=self.state_manager,
            )

            # Execute steps
            for step_index, step in enumerate(playbook.steps):
                execution_state.current_step_index = step_index

                # Check control signals
                try:
                    await self.state_manager.check_control_signal()
                except asyncio.CancelledError:
                    execution_state.status = ExecutionStatus.CANCELLED
                    execution_state.completed_at = datetime.now()
                    await self._notify_update(execution_state)
                    if self.database:
                        await self._save_execution_end(execution_state)
                    return execution_state

                # Check if skip requested
                if self.state_manager.is_skip_requested():
                    logger.info(f"Skipping step: {step.name}")
                    step_result = StepResult(
                        step_id=step.id,
                        step_name=step.name,
                        status=StepStatus.SKIPPED,
                        started_at=datetime.now(),
                        completed_at=datetime.now(),
                    )
                    execution_state.add_step_result(step_result)
                    self.state_manager.clear_skip()
                    await self._notify_update(execution_state)
                    if self.database:
                        await self._save_step_result(execution_state, step_result)
                    continue

                # Execute step
                logger.info(f"Executing step {step_index + 1}/{len(playbook.steps)}: {step.name}")
                step_result = await executor.execute_step(step)
                execution_state.add_step_result(step_result)

                # Handle set_variable step
                if step.type.value == "utility.set_variable" and step_result.output:
                    var_name = step_result.output.get("variable")
                    var_value = step_result.output.get("value")
                    if var_name:
                        execution_state.variables[var_name] = var_value
                        logger.info(f"Set variable: {var_name} = {var_value}")

                # Notify update
                await self._notify_update(execution_state)

                # Save to database
                if self.database:
                    await self._save_step_result(execution_state, step_result)

                # Handle failure
                if step_result.status == StepStatus.FAILED:
                    logger.error(f"Step failed: {step.name} - {step_result.error}")

                    if step.on_failure == OnFailureAction.ABORT:
                        execution_state.status = ExecutionStatus.FAILED
                        execution_state.error = f"Step '{step.id}' failed: {step_result.error}"
                        execution_state.completed_at = datetime.now()
                        await self._notify_update(execution_state)
                        if self.database:
                            await self._save_execution_end(execution_state)
                        return execution_state

                    elif step.on_failure == OnFailureAction.CONTINUE:
                        logger.warning(f"Continuing after failure (on_failure=continue)")
                        continue

                    elif step.on_failure == OnFailureAction.ROLLBACK:
                        logger.warning("Rollback not yet implemented, aborting")
                        execution_state.status = ExecutionStatus.FAILED
                        execution_state.error = f"Step '{step.id}' failed (rollback requested but not implemented)"
                        execution_state.completed_at = datetime.now()
                        await self._notify_update(execution_state)
                        if self.database:
                            await self._save_execution_end(execution_state)
                        return execution_state

            # All steps completed
            execution_state.status = ExecutionStatus.COMPLETED
            execution_state.completed_at = datetime.now()
            logger.info(f"Playbook execution completed: {playbook.name}")

        except Exception as e:
            logger.exception(f"Playbook execution error: {e}")
            execution_state.status = ExecutionStatus.FAILED
            execution_state.error = str(e)
            execution_state.completed_at = datetime.now()

        finally:
            # Stop browser manager if created
            if browser_manager:
                try:
                    await browser_manager.stop_screenshot_streaming()
                    await browser_manager.stop()
                    logger.info("Browser screenshot streaming stopped")
                except Exception as e:
                    logger.warning(f"Error stopping browser manager: {e}")
                finally:
                    self._browser_manager = None  # Clear reference

            # Notify final update
            await self._notify_update(execution_state)

            # Save to database
            if self.database:
                await self._save_execution_end(execution_state)

            self._current_execution = None

        return execution_state

    def _validate_parameters(self, playbook: Playbook, parameters: Dict[str, Any]) -> None:
        """
        Validate provided parameters against playbook definition

        Args:
            playbook: Playbook definition
            parameters: Provided parameters

        Raises:
            PlaybookExecutionError: If parameters are invalid
        """
        for param_def in playbook.parameters:
            value = parameters.get(param_def.name, param_def.default)
            try:
                param_def.validate(value)
            except ValueError as e:
                raise PlaybookExecutionError(f"Parameter validation failed: {e}")

    async def _notify_update(self, execution_state: ExecutionState) -> None:
        """
        Notify callback of execution update

        Args:
            execution_state: Current execution state
        """
        if self._update_callback:
            try:
                if asyncio.iscoroutinefunction(self._update_callback):
                    await self._update_callback(execution_state)
                else:
                    self._update_callback(execution_state)
            except Exception as e:
                logger.exception(f"Error in update callback: {e}")

    async def _save_execution_start(
        self, execution_state: ExecutionState, playbook: Playbook, parameters: Dict[str, Any]
    ) -> None:
        """Save execution start to database"""
        try:
            with self.database.session_scope() as session:
                execution_model = ExecutionModel(
                    execution_id=execution_state.execution_id,  # Save UUID
                    playbook_name=execution_state.playbook_name,
                    status=execution_state.status.value,
                    started_at=execution_state.started_at,
                    config_data=parameters,
                    playbook_version=playbook.version,
                )
                session.add(execution_model)
                session.flush()  # Get the auto-generated ID
                # Store the database ID for later queries
                execution_state.db_execution_id = execution_model.id
        except Exception as e:
            logger.exception(f"Error saving execution to database: {e}")

    async def _save_execution_end(self, execution_state: ExecutionState) -> None:
        """Save execution end to database"""
        try:
            with self.database.session_scope() as session:
                if not hasattr(execution_state, 'db_execution_id'):
                    logger.warning("No database execution ID found, skipping save")
                    return
                execution_model = (
                    session.query(ExecutionModel)
                    .filter_by(id=execution_state.db_execution_id)
                    .first()
                )
                if execution_model:
                    execution_model.status = execution_state.status.value
                    execution_model.completed_at = execution_state.completed_at
                    execution_model.error_message = execution_state.error
        except Exception as e:
            logger.exception(f"Error updating execution in database: {e}")

    async def _save_step_result(
        self, execution_state: ExecutionState, step_result: StepResult
    ) -> None:
        """Save step result to database"""
        try:
            if not hasattr(execution_state, 'db_execution_id'):
                logger.warning("No database execution ID found, skipping step result save")
                return
            with self.database.session_scope() as session:
                step_model = StepResultModel(
                    execution_id=execution_state.db_execution_id,
                    step_id=step_result.step_id,
                    step_name=step_result.step_name,
                    status=step_result.status.value,
                    started_at=step_result.started_at,
                    completed_at=step_result.completed_at,
                    output=step_result.output,
                    error_message=step_result.error,
                )
                session.add(step_model)
        except Exception as e:
            logger.exception(f"Error saving step result to database: {e}")

    async def pause(self) -> None:
        """Pause execution after current step"""
        await self.state_manager.pause()
        # Also pause browser screenshot streaming (freezes current frame)
        if self._browser_manager:
            self._browser_manager.pause_screenshot_streaming()
            logger.info("Browser screenshot streaming paused")

    async def resume(self) -> None:
        """Resume paused execution"""
        await self.state_manager.resume()
        # Also resume browser screenshot streaming
        if self._browser_manager:
            self._browser_manager.resume_screenshot_streaming()
            logger.info("Browser screenshot streaming resumed")

    async def skip_current_step(self) -> None:
        """Skip current step"""
        await self.state_manager.skip_current_step()

    async def cancel(self) -> None:
        """Cancel execution"""
        await self.state_manager.cancel()

    def get_current_execution(self) -> Optional[ExecutionState]:
        """
        Get current execution state

        Returns:
            Current execution state or None
        """
        return self._current_execution
