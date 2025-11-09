"""
AI Assistant - AI-powered test generation, validation, and debugging

Integrates with Anthropic's Claude API for intelligent assistance with playbook
execution, debugging, and test generation.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """Response from AI assistant"""

    success: bool
    content: str
    confidence: float = 0.0
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AIAssistant:
    """
    AI Assistant for test generation and validation

    Example (Future):
        assistant = AIAssistant(api_key="...")
        response = await assistant.generate_test_steps(
            description="Test login flow",
            context={"url": "http://example.com"}
        )
    """

    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-5-20250929"):
        """
        Initialize AI assistant

        Args:
            api_key: Anthropic API key (optional, will read from ANTHROPIC_API_KEY env var)
            model: Model to use (default: claude-sonnet-4-5-20250929)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self._client = None

        if self.api_key:
            try:
                from anthropic import Anthropic

                self._client = Anthropic(api_key=self.api_key)
                logger.info(f"AI Assistant initialized with model: {model}")
            except ImportError:
                logger.error("Anthropic SDK not installed. Install with: pip install anthropic")
                self._client = None
        else:
            logger.warning("AI Assistant initialized without API key (placeholder mode)")

    async def generate_test_steps(
        self, description: str, context: dict[str, Any] | None = None
    ) -> AIResponse:
        """
        Generate test steps from description

        Args:
            description: What to test
            context: Additional context

        Returns:
            AIResponse with generated steps
        """
        logger.info(f"AI: Generate test steps for: {description}")

        # Placeholder implementation
        return AIResponse(
            success=False,
            content="AI generation not yet implemented. This is a placeholder for future functionality.",
            confidence=0.0,
            metadata={"phase": "placeholder", "description": description},
        )

    async def validate_result(
        self, expected: str, actual: str, context: dict[str, Any] | None = None
    ) -> AIResponse:
        """
        Validate test result using AI

        Args:
            expected: Expected outcome description
            actual: Actual result
            context: Additional context

        Returns:
            AIResponse with validation result
        """
        logger.info(f"AI: Validate result - Expected: {expected}")

        # Placeholder implementation
        return AIResponse(
            success=False,
            content="AI validation not yet implemented. This is a placeholder for future functionality.",
            confidence=0.0,
            metadata={"phase": "placeholder", "expected": expected, "actual": actual},
        )

    async def analyze_screenshot(self, screenshot_path: str, question: str) -> AIResponse:
        """
        Analyze screenshot using AI vision

        Args:
            screenshot_path: Path to screenshot
            question: What to analyze

        Returns:
            AIResponse with analysis
        """
        logger.info(f"AI: Analyze screenshot: {screenshot_path}")

        # Placeholder implementation
        return AIResponse(
            success=False,
            content="AI vision analysis not yet implemented. This is a placeholder for future functionality.",
            confidence=0.0,
            metadata={"phase": "placeholder", "screenshot": screenshot_path, "question": question},
        )

    async def generate_assertion(
        self, description: str, context: dict[str, Any] | None = None
    ) -> AIResponse:
        """
        Generate assertion code from description

        Args:
            description: What to assert
            context: Additional context

        Returns:
            AIResponse with assertion code
        """
        logger.info(f"AI: Generate assertion for: {description}")

        # Placeholder implementation
        return AIResponse(
            success=False,
            content="AI assertion generation not yet implemented. This is a placeholder for future functionality.",
            confidence=0.0,
            metadata={"phase": "placeholder", "description": description},
        )

    async def debug_execution(self, user_question: str, execution_context: str) -> AIResponse:
        """
        Get AI assistance with debugging a failed playbook execution

        Args:
            user_question: User's question about the failure
            execution_context: Context about the execution (status, current step, errors)

        Returns:
            AIResponse with debugging suggestions
        """
        logger.info(f"AI: Debug execution - Question: {user_question}")

        if not self._client:
            return AIResponse(
                success=False,
                content="AI assistant not available. Please set ANTHROPIC_API_KEY environment variable.",
                confidence=0.0,
                metadata={"error": "no_api_key"},
            )

        try:
            # Build the system prompt for debugging
            system_prompt = """You are an expert debugging assistant for the Ignition Automation Toolkit.
You help users diagnose and fix issues with their playbook executions.

Your role:
- Analyze the execution context provided
- Understand what step is failing and why
- Suggest specific fixes (selector changes, timeout adjustments, etc.)
- Provide actionable recommendations

Be concise but thorough. Focus on practical solutions."""

            # Build the user message with context
            user_message = f"""**Execution Context:**
{execution_context}

**User Question:**
{user_question}

Please analyze the situation and provide specific recommendations to fix the issue."""

            # Call Claude API
            response = self._client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            # Extract the response text
            response_text = (
                response.content[0].text if response.content else "No response generated."
            )

            return AIResponse(
                success=True,
                content=response_text,
                confidence=1.0,
                metadata={
                    "model": self.model,
                    "usage": {
                        "input_tokens": (
                            response.usage.input_tokens if hasattr(response, "usage") else 0
                        ),
                        "output_tokens": (
                            response.usage.output_tokens if hasattr(response, "usage") else 0
                        ),
                    },
                },
            )

        except Exception as e:
            logger.error(f"AI debug execution error: {e}", exc_info=True)
            return AIResponse(
                success=False,
                content=f"Error calling AI service: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)},
            )

    async def analyze_page_for_fat(
        self,
        screenshot_b64: str,
        components: list[dict[str, Any]],
        context: str
    ) -> AIResponse:
        """
        Analyze Perspective page for FAT testing

        Args:
            screenshot_b64: Base64-encoded screenshot
            components: List of discovered components
            context: Additional context about the page

        Returns:
            AIResponse with component predictions and visual assessment
        """
        logger.info(f"AI: Analyze page for FAT - {len(components)} components")

        if not self._client:
            return AIResponse(
                success=False,
                content="AI assistant not available. Please set ANTHROPIC_API_KEY environment variable.",
                confidence=0.0,
                metadata={"error": "no_api_key"},
            )

        try:
            system_prompt = """You are an expert Perspective SCADA application tester for Factory Acceptance Testing (FAT).

Your task: Analyze a Perspective page screenshot and component inventory to:
1. Predict expected behavior for each interactive element
2. Assess visual clarity and consistency
3. Identify potential issues or concerns

For each component, predict:
- What should happen when clicked/interacted with
- How to verify it worked correctly
- Any visual concerns (clarity, consistency, accessibility)

Return your analysis as structured JSON with this format:
{
  "components": [
    {
      "id": "component-id",
      "predicted_behavior": "What should happen",
      "verification": "How to verify",
      "visual_assessment": "Visual quality assessment",
      "concerns": ["List of concerns if any"]
    }
  ],
  "overall_assessment": "Overall page quality assessment",
  "recommendations": ["List of testing recommendations"]
}

Be specific and actionable in your predictions."""

            import json
            components_json = json.dumps(components[:20], indent=2)  # Limit to first 20 for token efficiency

            user_message = f"""**Context:** {context}

**Components Found:** {len(components)} interactive elements

**Component Details (first 20):**
```json
{components_json}
```

Please analyze the screenshot and provide structured predictions for testing these components."""

            # Call Claude API with vision
            response = self._client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": screenshot_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": user_message
                        }
                    ]
                }]
            )

            response_text = (
                response.content[0].text if response.content else "{}"
            )

            # Try to parse as JSON
            try:
                import json
                predictions = json.loads(response_text)
            except json.JSONDecodeError:
                # If not valid JSON, wrap in structure
                predictions = {"raw_response": response_text}

            return AIResponse(
                success=True,
                content=response_text,
                confidence=0.9,
                metadata={
                    "model": self.model,
                    "predictions": predictions,
                    "component_count": len(components),
                    "usage": {
                        "input_tokens": (
                            response.usage.input_tokens if hasattr(response, "usage") else 0
                        ),
                        "output_tokens": (
                            response.usage.output_tokens if hasattr(response, "usage") else 0
                        ),
                    },
                },
            )

        except Exception as e:
            logger.error(f"AI page analysis error: {e}", exc_info=True)
            return AIResponse(
                success=False,
                content=f"Error calling AI service: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)},
            )

    async def generate_fat_test_cases(
        self,
        components: list[dict[str, Any]],
        analysis: dict[str, Any] | None = None,
        mode: str = "comprehensive"
    ) -> AIResponse:
        """
        Generate FAT test cases from component analysis

        Args:
            components: List of components to test
            analysis: Previous AI analysis (optional)
            mode: Test mode - "comprehensive", "smoke", or "critical_path"

        Returns:
            AIResponse with test plan
        """
        logger.info(f"AI: Generate FAT test cases - {len(components)} components, mode: {mode}")

        if not self._client:
            # Fallback: Generate basic test plan without AI
            logger.warning("AI not available - generating basic test plan")
            basic_plan = self._generate_basic_test_plan(components, mode)
            return AIResponse(
                success=True,
                content="Basic test plan generated (AI not available)",
                confidence=0.5,
                metadata={"test_plan": basic_plan, "fallback": True},
            )

        try:
            system_prompt = """You are an expert test engineer creating Factory Acceptance Test (FAT) plans for Perspective SCADA applications.

Your task: Generate a comprehensive test plan for the provided components.

For each component, create test cases with:
- component_id: Component identifier
- selector: CSS selector to target the element
- action: What action to perform (click, fill, etc.)
- expected: Expected outcome
- verify: How to verify success
- priority: high, medium, or low

Return as structured JSON:
{
  "test_plan": [
    {
      "component_id": "btn-start",
      "selector": "#btn-start",
      "action": "click",
      "expected": "Navigate to production view",
      "verify": "URL contains '/production' and page loads",
      "priority": "high"
    }
  ],
  "test_summary": {
    "total_tests": 10,
    "high_priority": 5,
    "medium_priority": 3,
    "low_priority": 2
  }
}

Prioritize based on mode: {mode}
- comprehensive: Test everything thoroughly
- smoke: Focus on critical functionality only
- critical_path: Test main user workflows"""

            import json
            components_json = json.dumps(components[:30], indent=2)
            analysis_json = json.dumps(analysis, indent=2) if analysis else "None"

            user_message = f"""**Test Mode:** {mode}

**Components to Test:**
```json
{components_json}
```

**Previous Analysis:**
```json
{analysis_json}
```

Generate a structured test plan for FAT testing."""

            response = self._client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )

            response_text = response.content[0].text if response.content else "{}"

            # Parse JSON response
            try:
                import json
                test_plan_data = json.loads(response_text)
                test_plan = test_plan_data.get("test_plan", [])
            except json.JSONDecodeError:
                logger.warning("AI response not valid JSON, using fallback")
                test_plan = self._generate_basic_test_plan(components, mode)

            return AIResponse(
                success=True,
                content=response_text,
                confidence=0.9,
                metadata={
                    "model": self.model,
                    "test_plan": test_plan,
                    "mode": mode,
                    "usage": {
                        "input_tokens": (
                            response.usage.input_tokens if hasattr(response, "usage") else 0
                        ),
                        "output_tokens": (
                            response.usage.output_tokens if hasattr(response, "usage") else 0
                        ),
                    },
                },
            )

        except Exception as e:
            logger.error(f"AI test generation error: {e}", exc_info=True)
            # Fallback to basic test plan
            basic_plan = self._generate_basic_test_plan(components, mode)
            return AIResponse(
                success=False,
                content=f"Error calling AI service, using fallback: {str(e)}",
                confidence=0.5,
                metadata={"test_plan": basic_plan, "error": str(e), "fallback": True},
            )

    def _generate_basic_test_plan(
        self,
        components: list[dict[str, Any]],
        mode: str = "comprehensive"
    ) -> list[dict[str, Any]]:
        """
        Generate basic test plan without AI (fallback)

        Args:
            components: Components to test
            mode: Test mode

        Returns:
            Basic test plan
        """
        test_plan = []

        for component in components:
            component_type = component.get("type", "unknown")
            component_id = component.get("id", "unknown")
            selector = component.get("selector", "")

            # Skip if in smoke mode and component is low priority
            if mode == "smoke" and component_type not in ["button", "link"]:
                continue

            # Generate basic test based on type
            if component_type == "button":
                test_plan.append({
                    "component_id": component_id,
                    "selector": selector,
                    "action": "click",
                    "expected": "Navigation or state change",
                    "verify": "No JavaScript errors",
                    "priority": "high"
                })
            elif component_type == "input":
                test_plan.append({
                    "component_id": component_id,
                    "selector": selector,
                    "action": "fill",
                    "value": "Test123",
                    "expected": "Input accepts text",
                    "verify": "Value updated",
                    "priority": "medium"
                })
            elif component_type == "link":
                test_plan.append({
                    "component_id": component_id,
                    "selector": selector,
                    "action": "click",
                    "expected": "Navigation",
                    "verify": "URL changed",
                    "priority": "high"
                })

        return test_plan

    async def verify_visual_consistency(
        self,
        screenshot_b64: str,
        guidelines: list[str]
    ) -> AIResponse:
        """
        Verify visual consistency against guidelines using AI vision

        Args:
            screenshot_b64: Base64-encoded screenshot
            guidelines: List of visual guidelines to check

        Returns:
            AIResponse with visual assessment
        """
        logger.info(f"AI: Verify visual consistency - {len(guidelines)} guidelines")

        if not self._client:
            return AIResponse(
                success=False,
                content="AI assistant not available for visual verification.",
                confidence=0.0,
                metadata={"error": "no_api_key"},
            )

        try:
            guidelines_text = "\n".join([f"- {g}" for g in guidelines])

            system_prompt = """You are an expert UI/UX designer reviewing Perspective SCADA interfaces for visual consistency and quality.

Your task: Analyze the screenshot against the provided visual guidelines and identify any violations or concerns.

Return as structured JSON:
{
  "compliance": {
    "passed": ["Guidelines that are met"],
    "failed": ["Guidelines that are violated"],
    "warnings": ["Potential issues to review"]
  },
  "issues_count": 5,
  "overall_assessment": "Overall visual quality assessment",
  "recommendations": ["Specific recommendations for improvements"]
}"""

            user_message = f"""**Visual Guidelines to Check:**
{guidelines_text}

Please analyze the screenshot and report on compliance with these guidelines."""

            response = self._client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": screenshot_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": user_message
                        }
                    ]
                }]
            )

            response_text = response.content[0].text if response.content else "{}"

            # Parse JSON
            try:
                import json
                report = json.loads(response_text)
            except json.JSONDecodeError:
                report = {"raw_response": response_text}

            return AIResponse(
                success=True,
                content=response_text,
                confidence=0.85,
                metadata={
                    "model": self.model,
                    "report": report,
                    "guidelines_count": len(guidelines),
                    "usage": {
                        "input_tokens": (
                            response.usage.input_tokens if hasattr(response, "usage") else 0
                        ),
                        "output_tokens": (
                            response.usage.output_tokens if hasattr(response, "usage") else 0
                        ),
                    },
                },
            )

        except Exception as e:
            logger.error(f"AI visual verification error: {e}", exc_info=True)
            return AIResponse(
                success=False,
                content=f"Error calling AI service: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)},
            )
