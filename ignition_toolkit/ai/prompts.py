"""
Prompt templates for AI operations

Provides structured prompts for various AI-assisted testing scenarios.
"""

from string import Template


class PromptTemplate:
    """
    Template system for AI prompts

    Example:
        template = PromptTemplate.TEST_GENERATION
        prompt = template.format(
            description="Login to Gateway",
            context="Gateway URL: http://localhost:8088"
        )
    """

    # Test step generation
    TEST_GENERATION = Template(
        """Generate test steps for the following scenario:

Description: $description

Context:
$context

Please provide a list of detailed test steps in YAML format compatible with the Ignition Automation Toolkit.
Include appropriate step types (gateway.*, browser.*, utility.*) and parameters.
"""
    )

    # Result validation
    RESULT_VALIDATION = Template(
        """Validate the following test result:

Expected: $expected

Actual: $actual

Context:
$context

Please determine if the actual result matches the expected outcome. Provide:
1. Pass/Fail determination
2. Confidence score (0-1)
3. Explanation of any discrepancies
"""
    )

    # Screenshot analysis
    SCREENSHOT_ANALYSIS = Template(
        """Analyze the screenshot and answer the following question:

Question: $question

Context:
$context

Please provide a detailed analysis based on what you see in the screenshot.
"""
    )

    # Assertion generation
    ASSERTION_GENERATION = Template(
        """Generate an assertion for the following requirement:

Requirement: $description

Context:
$context

Please provide Python assertion code that validates this requirement.
Use standard assertion patterns and provide clear error messages.
"""
    )

    # Playbook review
    PLAYBOOK_REVIEW = Template(
        """Review the following playbook for potential issues:

Playbook:
$playbook_yaml

Please identify:
1. Potential errors or misconfigurations
2. Missing error handling
3. Security concerns
4. Performance issues
5. Best practice violations

Provide specific recommendations for improvement.
"""
    )

    @staticmethod
    def format_template(template: Template, **kwargs) -> str:
        """
        Format template with values

        Args:
            template: Template to format
            **kwargs: Template variables

        Returns:
            Formatted prompt string
        """
        return template.safe_substitute(**kwargs)


# Predefined prompts for common scenarios
COMMON_PROMPTS = {
    "login_test": PromptTemplate.TEST_GENERATION.safe_substitute(
        description="Test user login functionality",
        context="Standard web login form with username and password fields",
    ),
    "module_upgrade": PromptTemplate.TEST_GENERATION.safe_substitute(
        description="Upgrade Ignition Gateway module",
        context="Upload .modl file, wait for installation, verify module is running",
    ),
    "health_check": PromptTemplate.TEST_GENERATION.safe_substitute(
        description="Verify Gateway health and connectivity",
        context="Check Gateway status, list modules and projects, verify all systems operational",
    ),
}
