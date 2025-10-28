"""
Tests for AI assistant functionality
"""

import os

import pytest

from ignition_toolkit.ai import AIAssistant


def test_ai_assistant_init_without_api_key():
    """Test AIAssistant can initialize without API key (placeholder mode)"""
    assistant = AIAssistant()
    assert assistant.api_key is None or assistant.api_key == ""
    assert assistant.model == "claude-sonnet-4-5-20250929"
    assert assistant._client is None


def test_ai_assistant_init_with_api_key():
    """Test AIAssistant initializes with API key"""
    assistant = AIAssistant(api_key="test-key-123")
    assert assistant.api_key == "test-key-123"
    assert assistant._client is not None


def test_ai_assistant_custom_model():
    """Test AIAssistant accepts custom model name"""
    assistant = AIAssistant(model="claude-3-opus-20240229")
    assert assistant.model == "claude-3-opus-20240229"


@pytest.mark.asyncio
async def test_generate_test_steps_placeholder():
    """Test generate_test_steps returns placeholder response"""
    assistant = AIAssistant()
    response = await assistant.generate_test_steps("Test login")

    assert response.success is False
    assert "placeholder" in response.content.lower()
    assert response.confidence == 0.0
    assert response.metadata.get("phase") == "placeholder"


@pytest.mark.asyncio
async def test_validate_result_placeholder():
    """Test validate_result returns placeholder response"""
    assistant = AIAssistant()
    response = await assistant.validate_result(expected="Status: OK", actual="Status: OK")

    assert response.success is False
    assert "placeholder" in response.content.lower()
    assert response.confidence == 0.0


@pytest.mark.asyncio
async def test_analyze_screenshot_placeholder():
    """Test analyze_screenshot returns placeholder response"""
    assistant = AIAssistant()
    response = await assistant.analyze_screenshot(
        screenshot_path="/tmp/screenshot.png", question="What do you see?"
    )

    assert response.success is False
    assert "placeholder" in response.content.lower()


@pytest.mark.asyncio
async def test_generate_assertion_placeholder():
    """Test generate_assertion returns placeholder response"""
    assistant = AIAssistant()
    response = await assistant.generate_assertion(description="Check status is 200")

    assert response.success is False
    assert "placeholder" in response.content.lower()


@pytest.mark.asyncio
async def test_debug_execution_no_api_key():
    """Test debug_execution returns error without API key"""
    # Ensure no API key is set
    original_key = os.environ.get("ANTHROPIC_API_KEY")
    if "ANTHROPIC_API_KEY" in os.environ:
        del os.environ["ANTHROPIC_API_KEY"]

    try:
        assistant = AIAssistant()
        response = await assistant.debug_execution(
            user_question="Why did this fail?", execution_context="Step 1 failed with timeout"
        )

        assert response.success is False
        assert "not available" in response.content.lower()
        assert response.metadata.get("error") == "no_api_key"
    finally:
        # Restore original key if it existed
        if original_key:
            os.environ["ANTHROPIC_API_KEY"] = original_key


@pytest.mark.asyncio
async def test_debug_execution_with_context():
    """Test debug_execution accepts execution context"""
    assistant = AIAssistant()

    execution_context = """
    Playbook: Gateway Login Test
    Current Step: 3 of 5
    Step Type: browser.click
    Selector: button#login
    Error: Element not found
    """

    response = await assistant.debug_execution(
        user_question="Why can't it find the login button?", execution_context=execution_context
    )

    # Should return error since no API key
    assert response.success is False
    assert response.metadata.get("error") == "no_api_key"


# Optional test - only runs if ANTHROPIC_API_KEY is set
@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"), reason="Requires ANTHROPIC_API_KEY environment variable"
)
@pytest.mark.asyncio
async def test_debug_execution_real_api():
    """Test debug_execution with real API call (requires API key)"""
    assistant = AIAssistant()
    response = await assistant.debug_execution(
        user_question="What is 2+2?", execution_context="Simple math test"
    )

    assert response.success is True
    assert len(response.content) > 0
    assert response.confidence == 1.0
    assert "model" in response.metadata
    assert response.metadata["model"] == "claude-sonnet-4-5-20250929"


def test_ai_response_dataclass():
    """Test AIResponse dataclass"""
    from ignition_toolkit.ai.assistant import AIResponse

    # Test with metadata
    response = AIResponse(
        success=True, content="Test response", confidence=0.9, metadata={"key": "value"}
    )
    assert response.success is True
    assert response.content == "Test response"
    assert response.confidence == 0.9
    assert response.metadata["key"] == "value"

    # Test without metadata (should auto-initialize to empty dict)
    response2 = AIResponse(
        success=False,
        content="Error",
    )
    assert response2.metadata == {}
