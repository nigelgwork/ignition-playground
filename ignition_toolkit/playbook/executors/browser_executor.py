"""
Browser step handlers

Handles all browser automation step types using Strategy Pattern.
"""

import logging
from datetime import datetime
from typing import Any

from ignition_toolkit.browser import BrowserManager
from ignition_toolkit.playbook.exceptions import StepExecutionError
from ignition_toolkit.playbook.executors.base import StepHandler

logger = logging.getLogger(__name__)


class BrowserNavigateHandler(StepHandler):
    """Handle browser.navigate step"""

    def __init__(self, manager: BrowserManager):
        self.manager = manager

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        url = params.get("url")
        wait_until = params.get("wait_until", "load")
        await self.manager.navigate(url, wait_until=wait_until)
        return {"url": url, "status": "navigated"}


class BrowserClickHandler(StepHandler):
    """Handle browser.click step"""

    def __init__(self, manager: BrowserManager):
        self.manager = manager

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        selector = params.get("selector")
        timeout = params.get("timeout", 30000)
        await self.manager.click(selector, timeout=timeout)
        return {"selector": selector, "status": "clicked"}


class BrowserFillHandler(StepHandler):
    """Handle browser.fill step"""

    def __init__(self, manager: BrowserManager):
        self.manager = manager

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        selector = params.get("selector")
        value = params.get("value")
        timeout = params.get("timeout", 30000)
        await self.manager.fill(selector, value, timeout=timeout)
        return {"selector": selector, "status": "filled"}


class BrowserScreenshotHandler(StepHandler):
    """Handle browser.screenshot step"""

    def __init__(self, manager: BrowserManager):
        self.manager = manager

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name", f"screenshot_{datetime.now().timestamp()}")
        full_page = params.get("full_page", False)
        screenshot_path = await self.manager.screenshot(name, full_page=full_page)
        return {"screenshot": str(screenshot_path), "status": "captured"}


class BrowserWaitHandler(StepHandler):
    """Handle browser.wait step"""

    def __init__(self, manager: BrowserManager):
        self.manager = manager

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        selector = params.get("selector")
        timeout = params.get("timeout", 30000)
        await self.manager.wait_for_selector(selector, timeout=timeout)
        return {"selector": selector, "status": "found"}


class BrowserVerifyHandler(StepHandler):
    """Handle browser.verify step"""

    def __init__(self, manager: BrowserManager):
        self.manager = manager

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        selector = params.get("selector")
        exists = params.get("exists", True)  # Default: verify element exists
        timeout = params.get("timeout", 5000)  # Shorter timeout for verification

        try:
            # Try to find the element
            await self.manager.wait_for_selector(selector, timeout=timeout)
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
