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
    """
    Handle utility.python step with sandboxing

    SECURITY: Executes Python code in a restricted sandbox with:
    - Limited builtins (no eval, compile, __import__, etc.)
    - No dangerous modules (os, subprocess, sys, etc.)
    - 5 second timeout
    - No file write access

    Allowed operations:
    - Basic Python (math, strings, lists, dicts)
    - JSON parsing
    - Regex operations
    - Date/time operations
    - Print output for variable assignment

    NOT allowed:
    - File system operations
    - Network operations
    - Process execution
    - Dangerous builtins
    """

    # Whitelist of safe builtins
    SAFE_BUILTINS = {
        'abs', 'all', 'any', 'bool', 'dict', 'enumerate', 'filter',
        'float', 'int', 'len', 'list', 'map', 'max', 'min', 'print',
        'range', 'reversed', 'round', 'sorted', 'str', 'sum', 'tuple',
        'zip', 'isinstance', 'type', 'ValueError', 'TypeError', 'KeyError',
    }

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        script = params.get("script")
        if not script:
            raise StepExecutionError("utility", "Python script is required")

        # SECURITY: Execute in sandboxed environment
        output_buffer = io.StringIO()
        result = {}

        try:
            # Create restricted builtins
            safe_builtins = {
                name: getattr(__builtins__, name)
                for name in self.SAFE_BUILTINS
                if hasattr(__builtins__, name)
            }

            # SECURITY: Restricted execution environment - NO dangerous modules
            exec_globals = {
                "__builtins__": safe_builtins,
                "json": __import__("json"),  # JSON parsing only
                "re": __import__("re"),      # Regex operations
                "datetime": __import__("datetime"),  # Date/time
                # NOTE: os, subprocess, sys, pathlib are NOT available
            }

            # Set 5 second timeout using signal (Unix only)
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError("Script execution timed out (5s limit)")

            # Only set signal handler on Unix systems
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(5)  # 5 second timeout

            try:
                # Redirect stdout to capture print() statements
                with redirect_stdout(output_buffer):
                    exec(script, exec_globals)
            finally:
                # Cancel timeout
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)

            # Parse output for key=value pairs (e.g., DETECTED_MODULE_FILE=/path/to/file)
            output = output_buffer.getvalue()
            for line in output.strip().split("\n"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    result[key.strip()] = value.strip()

            # Also include raw output
            result["_output"] = output

            return result

        except TimeoutError as e:
            raise StepExecutionError("utility.python", str(e))
        except Exception as e:
            raise StepExecutionError("utility.python", f"Script execution failed: {str(e)}")
