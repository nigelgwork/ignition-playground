"""
AI FAT testing step handlers

Handles AI-assisted Factory Acceptance Testing operations including
page analysis, test case generation, and visual consistency verification.
"""

import base64
import logging
from typing import Any

from ignition_toolkit.ai import AIAssistant
from ignition_toolkit.browser import BrowserManager
from ignition_toolkit.playbook.exceptions import StepExecutionError
from ignition_toolkit.playbook.executors.base import StepHandler

logger = logging.getLogger(__name__)


class AIAnalyzePageStructureHandler(StepHandler):
    """Handle ai.analyze_page_structure step - AI page analysis for FAT"""

    def __init__(self, ai_assistant: AIAssistant | None, browser_manager: BrowserManager | None):
        self.ai_assistant = ai_assistant
        self.browser_manager = browser_manager

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        screenshot = params.get("screenshot")
        components = params.get("components", [])
        context = params.get("context", "")

        if not self.ai_assistant:
            logger.warning("AI assistant not available - skipping page analysis")
            return {
                "status": "skipped",
                "reason": "AI assistant not available",
                "predictions": {}
            }

        # Get screenshot as base64
        screenshot_b64 = None

        if screenshot:
            # If screenshot is a file path, read it
            try:
                from pathlib import Path
                screenshot_path = Path(screenshot)
                if screenshot_path.exists():
                    with open(screenshot_path, "rb") as f:
                        screenshot_bytes = f.read()
                        screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
            except Exception as e:
                logger.warning(f"Failed to load screenshot from {screenshot}: {e}")

        # Fallback: capture fresh screenshot if browser available
        if not screenshot_b64 and self.browser_manager:
            try:
                screenshot_b64 = await self.browser_manager.get_screenshot_base64()
            except Exception as e:
                logger.warning(f"Failed to capture screenshot: {e}")

        if not screenshot_b64:
            raise StepExecutionError(
                "ai",
                "No screenshot available for AI analysis"
            )

        # Call AI assistant
        result = await self.ai_assistant.analyze_page_for_fat(
            screenshot_b64=screenshot_b64,
            components=components,
            context=context
        )

        if not result.success:
            raise StepExecutionError("ai", f"AI analysis failed: {result.content}")

        predictions = result.metadata.get("predictions", {})

        logger.info(f"AI page analysis completed - {len(components)} components analyzed")

        return {
            "status": "analyzed",
            "predictions": predictions,
            "confidence": result.confidence,
            "content": result.content,
            "component_count": len(components)
        }


class AIGenerateTestCasesHandler(StepHandler):
    """Handle ai.generate_test_cases step - AI test plan generation"""

    def __init__(self, ai_assistant: AIAssistant | None):
        self.ai_assistant = ai_assistant

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        components = params.get("components", [])
        analysis = params.get("analysis")
        mode = params.get("mode", "comprehensive")

        if not components:
            raise StepExecutionError(
                "ai",
                "No components provided for test case generation"
            )

        # Call AI assistant (with fallback if not available)
        if self.ai_assistant:
            result = await self.ai_assistant.generate_fat_test_cases(
                components=components,
                analysis=analysis,
                mode=mode
            )
        else:
            # Generate basic test plan without AI
            logger.warning("AI assistant not available - using basic test plan")
            from ignition_toolkit.ai.assistant import AIAssistant
            temp_assistant = AIAssistant()  # No API key = fallback mode
            result = await temp_assistant.generate_fat_test_cases(
                components=components,
                analysis=analysis,
                mode=mode
            )

        test_plan = result.metadata.get("test_plan", [])
        is_fallback = result.metadata.get("fallback", False)

        logger.info(
            f"Generated {len(test_plan)} test cases "
            f"(mode: {mode}, AI: {'fallback' if is_fallback else 'full'})"
        )

        return {
            "status": "generated",
            "test_plan": test_plan,
            "test_count": len(test_plan),
            "mode": mode,
            "confidence": result.confidence,
            "fallback": is_fallback
        }


class AIVerifyVisualConsistencyHandler(StepHandler):
    """Handle ai.verify_visual_consistency step - AI visual verification"""

    def __init__(self, ai_assistant: AIAssistant | None, browser_manager: BrowserManager | None):
        self.ai_assistant = ai_assistant
        self.browser_manager = browser_manager

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        screenshot = params.get("screenshot")
        guidelines = params.get("guidelines", [])

        if not self.ai_assistant:
            logger.warning("AI assistant not available - skipping visual verification")
            return {
                "status": "skipped",
                "reason": "AI assistant not available",
                "report": {},
                "issues_count": 0
            }

        if not guidelines:
            logger.warning("No visual guidelines provided - skipping verification")
            return {
                "status": "skipped",
                "reason": "No guidelines provided",
                "report": {},
                "issues_count": 0
            }

        # Get screenshot as base64
        screenshot_b64 = None

        if screenshot:
            try:
                from pathlib import Path
                screenshot_path = Path(screenshot)
                if screenshot_path.exists():
                    with open(screenshot_path, "rb") as f:
                        screenshot_bytes = f.read()
                        screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
            except Exception as e:
                logger.warning(f"Failed to load screenshot from {screenshot}: {e}")

        # Fallback: capture fresh screenshot
        if not screenshot_b64 and self.browser_manager:
            try:
                screenshot_b64 = await self.browser_manager.get_screenshot_base64()
            except Exception as e:
                logger.warning(f"Failed to capture screenshot: {e}")

        if not screenshot_b64:
            raise StepExecutionError(
                "ai",
                "No screenshot available for visual verification"
            )

        # Call AI assistant
        result = await self.ai_assistant.verify_visual_consistency(
            screenshot_b64=screenshot_b64,
            guidelines=guidelines
        )

        if not result.success:
            logger.warning(f"Visual verification failed: {result.content}")
            return {
                "status": "error",
                "error": result.content,
                "report": {},
                "issues_count": 0
            }

        report = result.metadata.get("report", {})
        issues_count = report.get("issues_count", 0)

        logger.info(
            f"Visual consistency check completed - "
            f"{issues_count} issues found against {len(guidelines)} guidelines"
        )

        return {
            "status": "verified",
            "report": report,
            "issues_count": issues_count,
            "guidelines_count": len(guidelines),
            "confidence": result.confidence
        }
