"""
Step executor - Execute individual playbook steps

Handles execution of different step types with proper error handling and retries.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ignition_toolkit.ai import AIAssistant
from ignition_toolkit.browser import BrowserManager
from ignition_toolkit.designer import DesignerManager
from ignition_toolkit.gateway import GatewayClient
from ignition_toolkit.playbook.exceptions import StepExecutionError
from ignition_toolkit.playbook.models import PlaybookStep, StepResult, StepStatus, StepType
from ignition_toolkit.playbook.parameters import ParameterResolver

logger = logging.getLogger(__name__)


class StepExecutor:
    """
    Execute individual playbook steps

    Example:
        executor = StepExecutor(gateway_client=client, resolver=resolver)
        result = await executor.execute_step(step)
    """

    def __init__(
        self,
        gateway_client: GatewayClient | None = None,
        browser_manager: BrowserManager | None = None,
        designer_manager: DesignerManager | None = None,
        ai_assistant: AIAssistant | None = None,
        parameter_resolver: ParameterResolver | None = None,
        base_path: Path | None = None,
        state_manager: Any | None = None,  # StateManager type hint causes circular import
    ):
        """
        Initialize step executor

        Args:
            gateway_client: Gateway client for gateway operations
            browser_manager: Browser manager for browser operations
            designer_manager: Designer manager for designer operations
            ai_assistant: AI assistant for AI operations
            parameter_resolver: Parameter resolver for resolving references
            base_path: Base path for resolving relative file paths
            state_manager: State manager for pause/resume and debug mode
        """
        self.gateway_client = gateway_client
        self.browser_manager = browser_manager
        self.designer_manager = designer_manager
        self.ai_assistant = ai_assistant
        self.parameter_resolver = parameter_resolver
        self.base_path = base_path or Path.cwd()
        self.state_manager = state_manager

    async def execute_step(self, step: PlaybookStep) -> StepResult:
        """
        Execute a single step with retries

        Args:
            step: Step to execute

        Returns:
            Step execution result
        """
        result = StepResult(
            step_id=step.id,
            step_name=step.name,
            status=StepStatus.RUNNING,
            started_at=datetime.now(),
        )

        retry_count = 0
        last_error = None

        while retry_count <= step.retry_count:
            try:
                # Execute step with timeout
                output = await asyncio.wait_for(self._execute_step_impl(step), timeout=step.timeout)

                # Success
                result.status = StepStatus.COMPLETED
                result.completed_at = datetime.now()
                result.output = output
                result.retry_count = retry_count
                return result

            except asyncio.TimeoutError:
                last_error = f"Step timed out after {step.timeout} seconds"
                logger.warning(f"Step {step.id} timed out (attempt {retry_count + 1})")

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Step {step.id} failed (attempt {retry_count + 1}): {e}")

            # Check if debug mode is enabled - if so, pause on first failure
            if (
                self.state_manager
                and self.state_manager.is_debug_mode_enabled()
                and retry_count == 0  # Only on first failure
            ):
                logger.info("Debug mode enabled - capturing context and pausing")
                debug_context = await self._capture_debug_context(step, last_error)
                await self.state_manager.trigger_debug_pause(debug_context)

                # Mark step as failed and return (no retries in debug mode)
                result.status = StepStatus.FAILED
                result.completed_at = datetime.now()
                result.error = last_error
                result.retry_count = 0
                return result

            # Increment retry count
            retry_count += 1

            # Wait before retry (unless this was the last attempt)
            if retry_count <= step.retry_count:
                logger.info(f"Retrying step {step.id} in {step.retry_delay} seconds...")
                await asyncio.sleep(step.retry_delay)

        # All retries exhausted
        result.status = StepStatus.FAILED
        result.completed_at = datetime.now()
        result.error = last_error
        result.retry_count = retry_count - 1
        return result

    async def _capture_debug_context(self, step: PlaybookStep, error: str) -> dict[str, Any]:
        """
        Capture debug context on failure

        Args:
            step: Failed step
            error: Error message

        Returns:
            Debug context dictionary
        """
        context = {
            "step_id": step.id,
            "step_name": step.name,
            "step_type": step.type.value,
            "step_parameters": step.parameters,
            "error": error,
            "timestamp": datetime.now().isoformat(),
        }

        # Capture screenshot and HTML if browser step
        if self.browser_manager and step.type.value.startswith("browser."):
            try:
                context["screenshot_base64"] = await self.browser_manager.get_screenshot_base64()
                context["page_html"] = await self.browser_manager.get_page_html()
                logger.info("Captured screenshot and HTML for debug context")
            except Exception as e:
                logger.warning(f"Failed to capture screenshot/HTML: {e}")
                context["capture_error"] = str(e)

        return context

    async def _execute_step_impl(self, step: PlaybookStep) -> dict[str, Any]:
        """
        Execute step implementation (without retries/timeout)

        Args:
            step: Step to execute

        Returns:
            Step output data

        Raises:
            StepExecutionError: If step fails
        """
        # Resolve parameters
        resolved_params = {}
        if self.parameter_resolver:
            resolved_params = self.parameter_resolver.resolve(step.parameters)
        else:
            resolved_params = step.parameters

        # Route to appropriate handler
        if step.type.value.startswith("gateway."):
            return await self._execute_gateway_step(step.type, resolved_params)
        elif step.type.value.startswith("browser."):
            return await self._execute_browser_step(step.type, resolved_params)
        elif step.type.value.startswith("designer."):
            return await self._execute_designer_step(step.type, resolved_params)
        elif step.type.value.startswith("playbook."):
            return await self._execute_playbook_step(step.type, resolved_params)
        elif step.type.value.startswith("utility."):
            return await self._execute_utility_step(step.type, resolved_params)
        elif step.type.value.startswith("ai."):
            return await self._execute_ai_step(step.type, resolved_params)
        else:
            raise StepExecutionError(step.id, f"Unknown step type: {step.type}")

    async def _execute_gateway_step(
        self, step_type: StepType, params: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute gateway operation step

        Args:
            step_type: Gateway step type
            params: Resolved parameters

        Returns:
            Step output

        Raises:
            StepExecutionError: If operation fails
        """
        if self.gateway_client is None:
            raise StepExecutionError("gateway", "No gateway client configured")

        try:
            if step_type == StepType.GATEWAY_LOGIN:
                username = params.get("username")
                password = params.get("password")
                # Handle credential object
                if hasattr(password, "password"):
                    password = password.password
                await self.gateway_client.login(username, password)
                return {"status": "logged_in"}

            elif step_type == StepType.GATEWAY_LOGOUT:
                await self.gateway_client.logout()
                return {"status": "logged_out"}

            elif step_type == StepType.GATEWAY_PING:
                result = await self.gateway_client.ping()
                return {"status": "ok", "response": result}

            elif step_type == StepType.GATEWAY_GET_INFO:
                info = await self.gateway_client.get_info()
                return {"info": info.__dict__}

            elif step_type == StepType.GATEWAY_GET_HEALTH:
                health = await self.gateway_client.get_health()
                return {"health": health.__dict__}

            elif step_type == StepType.GATEWAY_LIST_MODULES:
                modules = await self.gateway_client.list_modules()
                return {"modules": [m.__dict__ for m in modules], "count": len(modules)}

            elif step_type == StepType.GATEWAY_UPLOAD_MODULE:
                file_path = params.get("file")
                if self.parameter_resolver:
                    file_path = self.parameter_resolver.resolve_file_path(file_path, self.base_path)
                else:
                    file_path = Path(file_path)
                module_id = await self.gateway_client.upload_module(file_path)
                return {"module_id": module_id}

            elif step_type == StepType.GATEWAY_WAIT_MODULE:
                module_name = params.get("module_name")
                timeout = params.get("timeout", 300)
                await self.gateway_client.wait_for_module_installation(module_name, timeout)
                return {"status": "installed", "module_name": module_name}

            elif step_type == StepType.GATEWAY_LIST_PROJECTS:
                projects = await self.gateway_client.list_projects()
                return {"projects": [p.__dict__ for p in projects], "count": len(projects)}

            elif step_type == StepType.GATEWAY_GET_PROJECT:
                project_name = params.get("project_name")
                project = await self.gateway_client.get_project(project_name)
                return {"project": project.__dict__}

            elif step_type == StepType.GATEWAY_RESTART:
                wait_for_ready = params.get("wait_for_ready", False)
                await self.gateway_client.restart(wait_for_ready=wait_for_ready)
                return {"status": "restarted"}

            elif step_type == StepType.GATEWAY_WAIT_READY:
                timeout = params.get("timeout", 300)
                await self.gateway_client.wait_for_ready(timeout)
                return {"status": "ready"}

            else:
                raise StepExecutionError("gateway", f"Unknown gateway step type: {step_type}")

        except Exception as e:
            raise StepExecutionError("gateway", f"Gateway operation failed: {e}")

    async def _execute_browser_step(
        self, step_type: StepType, params: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute browser automation step

        Args:
            step_type: Browser step type
            params: Resolved parameters

        Returns:
            Step output

        Raises:
            StepExecutionError: If operation fails
        """
        if self.browser_manager is None:
            raise StepExecutionError("browser", "No browser manager configured")

        try:
            if step_type == StepType.BROWSER_NAVIGATE:
                url = params.get("url")
                wait_until = params.get("wait_until", "load")
                await self.browser_manager.navigate(url, wait_until=wait_until)
                return {"url": url, "status": "navigated"}

            elif step_type == StepType.BROWSER_CLICK:
                selector = params.get("selector")
                timeout = params.get("timeout", 30000)
                await self.browser_manager.click(selector, timeout=timeout)
                return {"selector": selector, "status": "clicked"}

            elif step_type == StepType.BROWSER_FILL:
                selector = params.get("selector")
                value = params.get("value")
                timeout = params.get("timeout", 30000)
                await self.browser_manager.fill(selector, value, timeout=timeout)
                return {"selector": selector, "status": "filled"}

            elif step_type == StepType.BROWSER_SCREENSHOT:
                name = params.get("name", f"screenshot_{datetime.now().timestamp()}")
                full_page = params.get("full_page", False)
                screenshot_path = await self.browser_manager.screenshot(name, full_page=full_page)
                return {"screenshot": str(screenshot_path), "status": "captured"}

            elif step_type == StepType.BROWSER_WAIT:
                selector = params.get("selector")
                timeout = params.get("timeout", 30000)
                await self.browser_manager.wait_for_selector(selector, timeout=timeout)
                return {"selector": selector, "status": "found"}

            elif step_type == StepType.BROWSER_VERIFY:
                selector = params.get("selector")
                exists = params.get("exists", True)  # Default: verify element exists
                timeout = params.get("timeout", 5000)  # Shorter timeout for verification

                try:
                    # Try to find the element
                    await self.browser_manager.wait_for_selector(selector, timeout=timeout)
                    element_found = True
                except Exception:
                    element_found = False

                # Check if result matches expectation
                if exists and not element_found:
                    raise StepExecutionError(
                        "browser",
                        f"Verification failed: Expected element '{selector}' to exist, but it was not found",
                    )
                elif not exists and element_found:
                    raise StepExecutionError(
                        "browser",
                        f"Verification failed: Expected element '{selector}' to NOT exist, but it was found",
                    )

                # Verification passed
                verification_result = "exists" if exists else "does not exist"
                return {
                    "selector": selector,
                    "exists": element_found,
                    "expected": exists,
                    "status": "verified",
                    "message": f"Element '{selector}' {verification_result} as expected",
                }

            else:
                raise StepExecutionError("browser", f"Unknown browser step type: {step_type}")

        except Exception as e:
            raise StepExecutionError("browser", f"Browser operation failed: {e}")

    async def _execute_designer_step(
        self, step_type: StepType, params: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute Designer desktop application step

        Args:
            step_type: Designer step type
            params: Resolved parameters

        Returns:
            Step output

        Raises:
            StepExecutionError: If operation fails
        """
        if self.designer_manager is None:
            raise StepExecutionError("designer", "No designer manager configured")

        try:
            if step_type == StepType.DESIGNER_LAUNCH:
                # Launch Designer from downloaded file
                launcher_file = params.get("launcher_file")
                if not launcher_file:
                    raise StepExecutionError("designer", "launcher_file parameter is required")

                from pathlib import Path
                launcher_path = Path(launcher_file)
                success = await self.designer_manager.launch_via_file(launcher_path)

                if not success:
                    raise StepExecutionError("designer", "Failed to launch Designer")

                return {"status": "launched", "launcher_file": str(launcher_path)}

            elif step_type == StepType.DESIGNER_LOGIN:
                username = params.get("username")
                password = params.get("password")

                # Handle credential object
                if hasattr(password, "password"):
                    password = password.password

                timeout = params.get("timeout", 30)
                success = await self.designer_manager.login(username, password, timeout=timeout)

                if not success:
                    raise StepExecutionError("designer", "Designer login failed")

                return {"status": "logged_in", "username": username}

            elif step_type == StepType.DESIGNER_OPEN_PROJECT:
                project_name = params.get("project_name")
                if not project_name:
                    # No project specified - stop here for manual selection
                    logger.info("No project_name specified - waiting for manual project selection")
                    return {"status": "awaiting_manual_selection"}

                timeout = params.get("timeout", 30)
                success = await self.designer_manager.open_project(project_name, timeout=timeout)

                if not success:
                    raise StepExecutionError("designer", f"Failed to open project: {project_name}")

                return {"status": "project_opened", "project": project_name}

            elif step_type == StepType.DESIGNER_CLOSE:
                success = await self.designer_manager.close()

                if not success:
                    raise StepExecutionError("designer", "Failed to close Designer")

                return {"status": "closed"}

            elif step_type == StepType.DESIGNER_SCREENSHOT:
                name = params.get("name", f"designer_screenshot_{datetime.now().timestamp()}")
                screenshot_path = await self.designer_manager.screenshot(name)
                return {"screenshot": str(screenshot_path), "status": "captured"}

            elif step_type == StepType.DESIGNER_WAIT:
                timeout = params.get("timeout", 30)
                success = await self.designer_manager.wait_for_window(timeout=timeout)

                if not success:
                    raise StepExecutionError("designer", "Designer window did not appear")

                return {"status": "window_found"}

            else:
                raise StepExecutionError("designer", f"Unknown designer step type: {step_type}")

        except Exception as e:
            raise StepExecutionError("designer", f"Designer operation failed: {e}")

    async def _execute_playbook_step(
        self, step_type: StepType, params: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute nested playbook as a single step (composable playbooks)

        Args:
            step_type: Playbook step type
            params: Resolved parameters

        Returns:
            Aggregated step output from nested playbook execution

        Raises:
            StepExecutionError: If playbook execution fails or validation fails
        """
        if step_type == StepType.PLAYBOOK_RUN:
            playbook_path = params.get("playbook")

            if not playbook_path:
                raise StepExecutionError("playbook", "Missing required parameter: playbook")

            # Convert to absolute path
            from ignition_toolkit.core.paths import get_playbooks_dir
            from ignition_toolkit.playbook.loader import PlaybookLoader
            from ignition_toolkit.playbook.metadata import PlaybookMetadataStore

            # PlaybookLoader has static methods only, no __init__
            metadata_store = PlaybookMetadataStore()

            # Resolve playbook path relative to playbooks root directory
            # (not relative to current playbook's directory)
            playbooks_root = get_playbooks_dir()
            full_path = playbooks_root / playbook_path

            if not full_path.exists():
                raise StepExecutionError("playbook", f"Playbook not found: {playbook_path}")

            # Get relative path for metadata lookup (relative to playbooks root)
            relative_path = playbook_path

            # Verify that playbook is marked as verified
            metadata = metadata_store.get_metadata(relative_path)
            if not metadata.verified:
                raise StepExecutionError(
                    "playbook",
                    f"Playbook '{relative_path}' must be verified before it can be used as a step. "
                    f"Mark it as verified via the UI 3-dot menu.",
                )

            # Check for circular dependencies (basic check)
            # TODO: Implement full call stack tracking for deeper nesting
            if hasattr(self, "_execution_stack"):
                if playbook_path in self._execution_stack:
                    raise StepExecutionError(
                        "playbook",
                        f"Circular dependency detected: playbook '{playbook_path}' calls itself",
                    )
            else:
                self._execution_stack = []

            # Add to execution stack
            self._execution_stack.append(playbook_path)

            # Check nesting depth
            MAX_NESTING_DEPTH = 3
            if len(self._execution_stack) > MAX_NESTING_DEPTH:
                self._execution_stack.pop()
                raise StepExecutionError(
                    "playbook",
                    f"Maximum nesting depth ({MAX_NESTING_DEPTH}) exceeded. "
                    f"Current stack: {' -> '.join(self._execution_stack)}",
                )

            try:
                # Load nested playbook using static method
                nested_playbook = PlaybookLoader.load_from_file(full_path)

                # Extract parameters for child playbook (remove 'playbook' key)
                child_params = {k: v for k, v in params.items() if k != "playbook"}

                # Execute nested playbook using EXISTING browser and gateway from parent
                # This allows browser context to persist across nested calls
                logger.info(f"Executing nested playbook: {playbook_path}")
                logger.info(f"Child parameters: {child_params}")

                # Create a child StepExecutor that shares browser and gateway from parent
                from ignition_toolkit.playbook.parameters import ParameterResolver

                # Create step_results dictionary for nested playbook
                nested_step_results: dict[str, dict[str, Any]] = {}

                child_resolver = ParameterResolver(
                    parameters=child_params,
                    variables={},
                    credential_vault=self.parameter_resolver.credential_vault if self.parameter_resolver else None,
                    step_results=nested_step_results,
                )

                child_executor = StepExecutor(
                    gateway_client=self.gateway_client,  # Share parent's gateway client
                    browser_manager=self.browser_manager,  # Share parent's browser manager
                    parameter_resolver=child_resolver,
                    base_path=self.base_path,
                    state_manager=self.state_manager,
                )
                child_executor._execution_stack = self._execution_stack.copy()

                # Execute all steps in the nested playbook
                nested_results = []
                nested_screenshots = []  # Track screenshots from nested execution

                for step in nested_playbook.steps:
                    logger.info(f"Executing nested step: {step.name}")
                    step_result = await child_executor.execute_step(step)

                    # Store step output for nested playbook step references
                    if step_result.output:
                        nested_step_results[step.id] = step_result.output

                    # Extract screenshot paths from step result output
                    if step_result.output and isinstance(step_result.output, dict):
                        # Check for direct screenshot (browser.screenshot steps)
                        screenshot = step_result.output.get("screenshot")
                        if screenshot and isinstance(screenshot, str):
                            nested_screenshots.append(screenshot)

                        # Check for nested playbook screenshots (recursive)
                        nested_playbook_screenshots = step_result.output.get("screenshots", [])
                        if isinstance(nested_playbook_screenshots, list):
                            nested_screenshots.extend(nested_playbook_screenshots)

                    # Store only JSON-serializable summary (not the full StepResult object)
                    nested_results.append({
                        "step_id": step.id,
                        "step_name": step.name,
                        "status": step_result.status.value if hasattr(step_result.status, 'value') else str(step_result.status),
                    })

                logger.info(f"Nested playbook '{playbook_path}' created {len(nested_screenshots)} screenshots")

                return {
                    "playbook": playbook_path,
                    "status": "completed",
                    "steps_executed": len(nested_results),
                    # Return summary of nested steps (nested steps are tracked separately in execution log)
                    "steps": nested_results,
                    # Track all screenshots created during nested execution (for cleanup on deletion)
                    "screenshots": nested_screenshots,
                }

            finally:
                # Remove from execution stack
                self._execution_stack.pop()

        else:
            raise StepExecutionError("playbook", f"Unknown playbook step type: {step_type}")

    async def _execute_utility_step(
        self, step_type: StepType, params: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute utility step

        Args:
            step_type: Utility step type
            params: Resolved parameters

        Returns:
            Step output

        Raises:
            StepExecutionError: If operation fails
        """
        if step_type == StepType.SLEEP:
            seconds = params.get("seconds", 1)
            await asyncio.sleep(seconds)
            return {"slept": seconds}

        elif step_type == StepType.LOG:
            message = params.get("message", "")
            level = params.get("level", "info").lower()
            if level == "debug":
                logger.debug(message)
            elif level == "info":
                logger.info(message)
            elif level == "warning":
                logger.warning(message)
            elif level == "error":
                logger.error(message)
            return {"logged": message, "level": level}

        elif step_type == StepType.SET_VARIABLE:
            name = params.get("name")
            value = params.get("value")
            if not name:
                raise StepExecutionError("utility", "Variable name is required")
            # Variable will be set by the engine
            return {"variable": name, "value": value}

        elif step_type == StepType.PYTHON:
            script = params.get("script")
            if not script:
                raise StepExecutionError("utility", "Python script is required")

            # Execute Python script in restricted environment
            import io
            import sys
            from contextlib import redirect_stdout

            # Capture stdout
            output_buffer = io.StringIO()
            result = {}

            try:
                # Create execution environment with access to common libraries
                exec_globals = {
                    "__builtins__": __builtins__,
                    "Path": __import__("pathlib").Path,
                    "zipfile": __import__("zipfile"),
                    "ET": __import__("xml.etree.ElementTree"),
                    "json": __import__("json"),
                    "os": __import__("os"),
                }

                # Redirect stdout to capture print() statements
                with redirect_stdout(output_buffer):
                    exec(script, exec_globals)

                # Parse output for key=value pairs (e.g., DETECTED_MODULE_FILE=/path/to/file)
                output = output_buffer.getvalue()
                for line in output.strip().split("\n"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        result[key] = value

                # Also include raw output
                result["_output"] = output

                return result

            except Exception as e:
                raise StepExecutionError("utility.python", f"Script execution failed: {str(e)}")

        else:
            raise StepExecutionError("utility", f"Unknown utility step type: {step_type}")

    async def _execute_ai_step(self, step_type: StepType, params: dict[str, Any]) -> dict[str, Any]:
        """
        Execute AI operation step (placeholder)

        Args:
            step_type: AI step type
            params: Resolved parameters

        Returns:
            Step output

        Raises:
            StepExecutionError: If operation fails
        """
        if self.ai_assistant is None:
            logger.warning("AI assistant not configured, using placeholder")
            self.ai_assistant = AIAssistant()

        try:
            if step_type == StepType.AI_GENERATE:
                description = params.get("description", "")
                context = params.get("context", {})
                response = await self.ai_assistant.generate_test_steps(description, context)
                return {
                    "success": response.success,
                    "content": response.content,
                    "confidence": response.confidence,
                    "metadata": response.metadata,
                }

            elif step_type == StepType.AI_VALIDATE:
                expected = params.get("expected", "")
                actual = params.get("actual", "")
                context = params.get("context", {})
                response = await self.ai_assistant.validate_result(expected, actual, context)
                return {
                    "success": response.success,
                    "content": response.content,
                    "confidence": response.confidence,
                    "metadata": response.metadata,
                }

            elif step_type == StepType.AI_ANALYZE:
                screenshot = params.get("screenshot", "")
                question = params.get("question", "")
                response = await self.ai_assistant.analyze_screenshot(screenshot, question)
                return {
                    "success": response.success,
                    "content": response.content,
                    "confidence": response.confidence,
                    "metadata": response.metadata,
                }

            else:
                raise StepExecutionError("ai", f"Unknown AI step type: {step_type}")

        except Exception as e:
            raise StepExecutionError("ai", f"AI operation failed: {e}")
