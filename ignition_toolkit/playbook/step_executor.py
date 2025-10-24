"""
Step executor - Execute individual playbook steps

Handles execution of different step types with proper error handling and retries.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import logging

from ignition_toolkit.gateway import GatewayClient
from ignition_toolkit.browser import BrowserManager
from ignition_toolkit.ai import AIAssistant
from ignition_toolkit.playbook.models import PlaybookStep, StepType, StepResult, StepStatus
from ignition_toolkit.playbook.parameters import ParameterResolver
from ignition_toolkit.playbook.exceptions import StepExecutionError

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
        gateway_client: Optional[GatewayClient] = None,
        browser_manager: Optional[BrowserManager] = None,
        ai_assistant: Optional[AIAssistant] = None,
        parameter_resolver: Optional[ParameterResolver] = None,
        base_path: Optional[Path] = None,
        state_manager: Optional[Any] = None,  # StateManager type hint causes circular import
    ):
        """
        Initialize step executor

        Args:
            gateway_client: Gateway client for gateway operations
            browser_manager: Browser manager for browser operations
            ai_assistant: AI assistant for AI operations
            parameter_resolver: Parameter resolver for resolving references
            base_path: Base path for resolving relative file paths
            state_manager: State manager for pause/resume and debug mode
        """
        self.gateway_client = gateway_client
        self.browser_manager = browser_manager
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
                output = await asyncio.wait_for(
                    self._execute_step_impl(step), timeout=step.timeout
                )

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

    async def _capture_debug_context(self, step: PlaybookStep, error: str) -> Dict[str, Any]:
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

    async def _execute_step_impl(self, step: PlaybookStep) -> Dict[str, Any]:
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
        elif step.type.value.startswith("utility."):
            return await self._execute_utility_step(step.type, resolved_params)
        elif step.type.value.startswith("ai."):
            return await self._execute_ai_step(step.type, resolved_params)
        else:
            raise StepExecutionError(step.id, f"Unknown step type: {step.type}")

    async def _execute_gateway_step(
        self, step_type: StepType, params: Dict[str, Any]
    ) -> Dict[str, Any]:
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
                    file_path = self.parameter_resolver.resolve_file_path(
                        file_path, self.base_path
                    )
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
        self, step_type: StepType, params: Dict[str, Any]
    ) -> Dict[str, Any]:
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

            else:
                raise StepExecutionError("browser", f"Unknown browser step type: {step_type}")

        except Exception as e:
            raise StepExecutionError("browser", f"Browser operation failed: {e}")

    async def _execute_utility_step(
        self, step_type: StepType, params: Dict[str, Any]
    ) -> Dict[str, Any]:
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

        else:
            raise StepExecutionError("utility", f"Unknown utility step type: {step_type}")

    async def _execute_ai_step(
        self, step_type: StepType, params: Dict[str, Any]
    ) -> Dict[str, Any]:
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
