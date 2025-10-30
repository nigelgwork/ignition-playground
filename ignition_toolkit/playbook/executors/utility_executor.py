"""
Utility step handlers

Handles all utility step types using Strategy Pattern.
"""

import asyncio
import io
import logging
import sys
from contextlib import redirect_stdout
from typing import Any

from ignition_toolkit.playbook.exceptions import StepExecutionError
from ignition_toolkit.playbook.executors.base import StepHandler

logger = logging.getLogger(__name__)


class UtilitySleepHandler(StepHandler):
    """Handle utility.sleep step"""

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        seconds = params.get("seconds", 1)
        await asyncio.sleep(seconds)
        return {"slept": seconds}


class UtilityLogHandler(StepHandler):
    """Handle utility.log step"""

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
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


class UtilitySetVariableHandler(StepHandler):
    """Handle utility.set_variable step"""

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        value = params.get("value")

        if not name:
            raise StepExecutionError("utility", "Variable name is required")

        # Variable will be set by the engine
        return {"variable": name, "value": value}


class UtilityPythonHandler(StepHandler):
    """Handle utility.python step"""

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        script = params.get("script")
        if not script:
            raise StepExecutionError("utility", "Python script is required")

        # Execute Python script in restricted environment
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
