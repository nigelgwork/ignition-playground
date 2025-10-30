"""
AI step handlers

Handles all AI operation step types using Strategy Pattern.
"""

import logging
from typing import Any

from ignition_toolkit.ai import AIAssistant
from ignition_toolkit.playbook.exceptions import StepExecutionError
from ignition_toolkit.playbook.executors.base import StepHandler

logger = logging.getLogger(__name__)


class AIGenerateHandler(StepHandler):
    """Handle ai.generate step"""

    def __init__(self, assistant: AIAssistant | None = None):
        if assistant is None:
            logger.warning("AI assistant not configured, using placeholder")
            assistant = AIAssistant()
        self.assistant = assistant

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        description = params.get("description", "")
        context = params.get("context", {})

        response = await self.assistant.generate_test_steps(description, context)

        return {
            "success": response.success,
            "content": response.content,
            "confidence": response.confidence,
            "metadata": response.metadata,
        }


class AIValidateHandler(StepHandler):
    """Handle ai.validate step"""

    def __init__(self, assistant: AIAssistant | None = None):
        if assistant is None:
            logger.warning("AI assistant not configured, using placeholder")
            assistant = AIAssistant()
        self.assistant = assistant

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        expected = params.get("expected", "")
        actual = params.get("actual", "")
        context = params.get("context", {})

        response = await self.assistant.validate_result(expected, actual, context)

        return {
            "success": response.success,
            "content": response.content,
            "confidence": response.confidence,
            "metadata": response.metadata,
        }


class AIAnalyzeHandler(StepHandler):
    """Handle ai.analyze step"""

    def __init__(self, assistant: AIAssistant | None = None):
        if assistant is None:
            logger.warning("AI assistant not configured, using placeholder")
            assistant = AIAssistant()
        self.assistant = assistant

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        screenshot = params.get("screenshot", "")
        question = params.get("question", "")

        response = await self.assistant.analyze_screenshot(screenshot, question)

        return {
            "success": response.success,
            "content": response.content,
            "confidence": response.confidence,
            "metadata": response.metadata,
        }
