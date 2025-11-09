"""
Perspective FAT testing step handlers

Handles Perspective-specific Factory Acceptance Testing (FAT) operations
including component discovery, test execution, and verification.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ignition_toolkit.browser import BrowserManager
from ignition_toolkit.playbook.exceptions import StepExecutionError
from ignition_toolkit.playbook.executors.base import StepHandler

logger = logging.getLogger(__name__)


class PerspectiveDiscoverPageHandler(StepHandler):
    """Handle perspective.discover_page step - Discover interactive components"""

    def __init__(self, manager: BrowserManager):
        self.manager = manager

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        selector = params.get("selector", "body")
        types = params.get("types", [])
        exclude_selectors = params.get("exclude_selectors", [])

        # Load discovery script
        script_path = Path(__file__).parent.parent.parent / "browser" / "component_discovery.js"

        if not script_path.exists():
            raise StepExecutionError(
                "perspective",
                f"Component discovery script not found: {script_path}"
            )

        with open(script_path, "r") as f:
            discovery_script = f.read()

        page = await self.manager.get_page()

        # Inject discovery script
        await page.evaluate(discovery_script)

        # Execute discovery
        options = {
            "types": types,
            "excludeSelectors": exclude_selectors
        }

        result = await page.evaluate(
            f"discoverPerspectiveComponents('{selector}', {json.dumps(options)})"
        )

        if not result.get("success"):
            raise StepExecutionError(
                "perspective",
                f"Component discovery failed: {result.get('error', 'Unknown error')}"
            )

        logger.info(
            f"Discovered {result.get('count', 0)} components "
            f"(types: {types or 'all'})"
        )

        return {
            "status": "discovered",
            "count": result.get("count", 0),
            "inventory": result.get("components", []),
            "timestamp": result.get("timestamp"),
            "root_selector": selector
        }


class PerspectiveExtractMetadataHandler(StepHandler):
    """Handle perspective.extract_component_metadata step - Enrich component metadata"""

    def __init__(self, manager: BrowserManager):
        self.manager = manager

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        components = params.get("components", [])

        if not components:
            logger.warning("No components provided for metadata extraction")
            return {
                "status": "skipped",
                "enriched_inventory": [],
                "count": 0
            }

        # Enrich each component with additional metadata
        enriched = []

        for component in components:
            enriched_component = {
                **component,
                "metadata": {
                    "analyzed_at": datetime.now().isoformat(),
                    "has_label": bool(component.get("label") or component.get("ariaLabel")),
                    "has_id": bool(component.get("id")),
                    "is_perspective_component": bool(component.get("componentPath")),
                    "selector_reliability": self._assess_selector_reliability(component)
                }
            }

            enriched.append(enriched_component)

        logger.info(f"Enriched metadata for {len(enriched)} components")

        return {
            "status": "enriched",
            "enriched_inventory": enriched,
            "count": len(enriched)
        }

    def _assess_selector_reliability(self, component: dict) -> str:
        """Assess reliability of component selectors"""
        if component.get("id"):
            return "high"  # ID is most reliable
        if component.get("componentPath"):
            return "high"  # Perspective component path is reliable
        if component.get("dataAttributes"):
            return "medium"  # Data attributes are fairly reliable
        return "low"  # CSS path only


class PerspectiveExecuteTestManifestHandler(StepHandler):
    """Handle perspective.execute_test_manifest step - Execute test plan"""

    def __init__(self, manager: BrowserManager):
        self.manager = manager

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        manifest = params.get("manifest", [])
        capture_screenshots = params.get("capture_screenshots", True)
        on_failure = params.get("on_failure", "continue")
        return_to_baseline = params.get("return_to_baseline", True)
        baseline_url = params.get("baseline_url")

        if not manifest:
            raise StepExecutionError(
                "perspective",
                "No test manifest provided"
            )

        page = await self.manager.get_page()
        results = []
        passed = 0
        failed = 0
        skipped = 0

        logger.info(f"Executing test manifest with {len(manifest)} tests")

        for test in manifest:
            component_id = test.get("component_id", "unknown")
            action = test.get("action", "click")
            expected = test.get("expected", "No error")

            logger.info(f"Testing component: {component_id} (action: {action})")

            test_result = {
                "component_id": component_id,
                "action": action,
                "expected": expected,
                "started_at": datetime.now().isoformat()
            }

            try:
                # Execute test action
                if action == "click":
                    selector = test.get("selector")
                    if not selector:
                        raise ValueError("No selector provided for click action")

                    await page.click(selector, timeout=5000)
                    await asyncio.sleep(0.5)  # Brief wait for UI response

                elif action == "fill":
                    selector = test.get("selector")
                    value = test.get("value", "Test")
                    if not selector:
                        raise ValueError("No selector provided for fill action")

                    await page.fill(selector, value, timeout=5000)

                else:
                    raise ValueError(f"Unsupported test action: {action}")

                # Capture screenshot if enabled
                if capture_screenshots:
                    screenshot_name = f"test_{component_id}_{datetime.now().timestamp()}"
                    screenshot_path = await self.manager.screenshot(screenshot_name)
                    test_result["screenshot"] = str(screenshot_path)

                # Mark as passed
                test_result["status"] = "passed"
                test_result["actual"] = "Action completed successfully"
                test_result["completed_at"] = datetime.now().isoformat()
                passed += 1

            except Exception as e:
                logger.warning(f"Test failed for {component_id}: {e}")
                test_result["status"] = "failed"
                test_result["error"] = str(e)
                test_result["actual"] = f"Error: {e}"
                test_result["completed_at"] = datetime.now().isoformat()
                failed += 1

                if on_failure == "abort":
                    results.append(test_result)
                    break

            results.append(test_result)

            # Return to baseline if configured
            if return_to_baseline and baseline_url:
                try:
                    await page.goto(baseline_url, wait_until="networkidle", timeout=10000)
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.warning(f"Failed to return to baseline: {e}")

        logger.info(
            f"Test execution complete: {passed} passed, {failed} failed, "
            f"{skipped} skipped (total: {len(results)})"
        )

        return {
            "status": "completed",
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "results": results
        }


class PerspectiveVerifyNavigationHandler(StepHandler):
    """Handle perspective.verify_navigation step - Verify navigation occurred"""

    def __init__(self, manager: BrowserManager):
        self.manager = manager

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        expected_url_pattern = params.get("expected_url_pattern")
        expected_title_pattern = params.get("expected_title_pattern")
        timeout = params.get("timeout", 5000)

        page = await self.manager.get_page()

        try:
            # Wait for navigation
            await page.wait_for_load_state("networkidle", timeout=timeout)

            current_url = page.url
            current_title = await page.title()

            # Verify URL if pattern provided
            if expected_url_pattern:
                if expected_url_pattern not in current_url:
                    raise StepExecutionError(
                        "perspective",
                        f"URL verification failed. Expected pattern: '{expected_url_pattern}', "
                        f"Actual URL: '{current_url}'"
                    )

            # Verify title if pattern provided
            if expected_title_pattern:
                if expected_title_pattern not in current_title:
                    raise StepExecutionError(
                        "perspective",
                        f"Title verification failed. Expected pattern: '{expected_title_pattern}', "
                        f"Actual title: '{current_title}'"
                    )

            return {
                "status": "verified",
                "url": current_url,
                "title": current_title,
                "message": "Navigation verified successfully"
            }

        except TimeoutError:
            raise StepExecutionError(
                "perspective",
                f"Navigation verification timed out after {timeout}ms"
            )


class PerspectiveVerifyDockHandler(StepHandler):
    """Handle perspective.verify_dock_opened step - Verify dock opened"""

    def __init__(self, manager: BrowserManager):
        self.manager = manager

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        dock_selector = params.get("dock_selector")
        timeout = params.get("timeout", 3000)

        if not dock_selector:
            raise StepExecutionError(
                "perspective",
                "No dock_selector provided"
            )

        page = await self.manager.get_page()

        try:
            # Wait for dock element to appear
            await page.wait_for_selector(dock_selector, timeout=timeout, state="visible")

            # Verify dock is visible
            is_visible = await page.is_visible(dock_selector)

            if not is_visible:
                raise StepExecutionError(
                    "perspective",
                    f"Dock element found but not visible: {dock_selector}"
                )

            return {
                "status": "verified",
                "dock_selector": dock_selector,
                "message": "Dock opened and visible"
            }

        except TimeoutError:
            raise StepExecutionError(
                "perspective",
                f"Dock did not open within {timeout}ms: {dock_selector}"
            )
