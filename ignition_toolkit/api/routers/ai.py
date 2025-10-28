"""
AI Assistant routes

Handles AI credentials, settings, assistance, and Claude Code integration.
"""

import logging
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ignition_toolkit.core.paths import get_playbooks_dir
from ignition_toolkit.storage import get_database

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["ai"])


# Dependency injection for global state
def get_active_engines():
    """Get shared active engines dict from app"""
    from ignition_toolkit.api.app import active_engines

    return active_engines


# ============================================================================
# Pydantic Models
# ============================================================================


class AICredentialCreate(BaseModel):
    """Request to create AI credential"""

    name: str  # Unique name for the credential
    provider: str  # "openai", "anthropic", "gemini", "local"
    api_key: str | None = None
    api_base_url: str | None = None  # For local LLMs
    model_name: str | None = None
    enabled: bool = False


class AICredentialInfo(BaseModel):
    """Response with AI credential info"""

    id: int
    name: str
    provider: str
    api_base_url: str | None
    model_name: str | None
    enabled: str  # "true" or "false"
    has_api_key: bool


# Legacy models for backward compatibility
class AISettingsRequest(BaseModel):
    """Request to save AI settings (legacy singleton)"""

    provider: str  # "openai", "anthropic", "local"
    api_key: str | None = None
    api_base_url: str | None = None  # For local LLMs
    model_name: str | None = None
    enabled: bool = False


class AISettingsResponse(BaseModel):
    """Response with AI settings (legacy singleton)"""

    id: int
    provider: str
    api_base_url: str | None
    model_name: str | None
    enabled: str  # "true" or "false"
    has_api_key: bool


class AIAssistRequest(BaseModel):
    """Request for AI assistance during execution"""

    execution_id: str
    user_message: str
    current_step_id: str | None = None
    error_context: str | None = None
    credential_name: str | None = None  # Name of AI credential to use


class AIAssistResponse(BaseModel):
    """Response from AI assistant"""

    message: str
    suggested_fix: dict[str, Any] | None = None
    can_auto_apply: bool = False


class ClaudeCodeSessionRequest(BaseModel):
    """Request to create a Claude Code debugging session"""

    execution_id: str


class ClaudeCodeSessionResponse(BaseModel):
    """Response with Claude Code session details"""

    command: str
    playbook_path: str
    execution_id: str
    context_message: str


@router.get("/api/ai-credentials", response_model=list[AICredentialInfo])
async def list_ai_credentials():
    """List all AI credentials"""
    database = get_database()
    with database.session_scope() as session:
        from ignition_toolkit.storage.models import AISettingsModel

        credentials = session.query(AISettingsModel).all()
        return [AICredentialInfo(**cred.to_dict()) for cred in credentials]


@router.post("/api/ai-credentials", response_model=AICredentialInfo)
async def create_ai_credential(request: AICredentialCreate):
    """Create a new AI credential"""
    database = get_database()
    with database.session_scope() as session:
        from ignition_toolkit.storage.models import AISettingsModel

        # Check if name already exists
        existing = session.query(AISettingsModel).filter_by(name=request.name).first()
        if existing:
            raise HTTPException(
                status_code=400, detail=f"AI credential with name '{request.name}' already exists"
            )

        credential = AISettingsModel(
            name=request.name,
            provider=request.provider,
            api_key=request.api_key,
            api_base_url=request.api_base_url,
            model_name=request.model_name,
            enabled="true" if request.enabled else "false",
        )
        session.add(credential)
        session.commit()
        session.refresh(credential)
        return AICredentialInfo(**credential.to_dict())


@router.put("/api/ai-credentials/{name}", response_model=AICredentialInfo)
async def update_ai_credential(name: str, request: AICredentialCreate):
    """Update an existing AI credential"""
    database = get_database()
    with database.session_scope() as session:
        from ignition_toolkit.storage.models import AISettingsModel

        credential = session.query(AISettingsModel).filter_by(name=name).first()
        if not credential:
            raise HTTPException(status_code=404, detail=f"AI credential '{name}' not found")

        # Update fields
        if request.name != name:
            # Check if new name conflicts
            existing = session.query(AISettingsModel).filter_by(name=request.name).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"AI credential with name '{request.name}' already exists",
                )
            credential.name = request.name

        credential.provider = request.provider
        if request.api_key:  # Only update if provided
            credential.api_key = request.api_key
        credential.api_base_url = request.api_base_url
        credential.model_name = request.model_name
        credential.enabled = "true" if request.enabled else "false"

        session.commit()
        session.refresh(credential)
        return AICredentialInfo(**credential.to_dict())


@router.delete("/api/ai-credentials/{name}", response_model=AICredentialInfo)
async def delete_ai_credential(name: str):
    """Delete an AI credential"""
    database = get_database()
    with database.session_scope() as session:
        from ignition_toolkit.storage.models import AISettingsModel

        credential = session.query(AISettingsModel).filter_by(name=name).first()
        if not credential:
            raise HTTPException(status_code=404, detail=f"AI credential '{name}' not found")

        result = AICredentialInfo(**credential.to_dict())
        session.delete(credential)
        session.commit()
        return result


# Legacy endpoints for backward compatibility
@router.get("/api/ai-settings", response_model=AISettingsResponse)
async def get_ai_settings():
    """Get AI settings (legacy singleton - returns first credential)"""
    database = get_database()
    with database.session_scope() as session:
        from ignition_toolkit.storage.models import AISettingsModel

        settings = session.query(AISettingsModel).first()
        if not settings:
            # Return default/empty settings
            return AISettingsResponse(
                id=0,
                provider="openai",
                api_base_url=None,
                model_name="gpt-4",
                enabled="false",
                has_api_key=False,
            )
        return AISettingsResponse(**settings.to_dict())


@router.post("/api/ai-settings", response_model=AISettingsResponse)
async def save_ai_settings(request: AISettingsRequest):
    """Save AI settings (legacy singleton - creates/updates first credential)"""
    database = get_database()
    with database.session_scope() as session:
        from ignition_toolkit.storage.models import AISettingsModel

        settings = session.query(AISettingsModel).first()
        if settings:
            # Update existing
            settings.provider = request.provider
            if request.api_key:  # Only update if provided
                settings.api_key = request.api_key
            settings.api_base_url = request.api_base_url
            settings.model_name = request.model_name
            settings.enabled = "true" if request.enabled else "false"
        else:
            # Create new with default name
            settings = AISettingsModel(
                name="default",
                provider=request.provider,
                api_key=request.api_key,
                api_base_url=request.api_base_url,
                model_name=request.model_name,
                enabled="true" if request.enabled else "false",
            )
            session.add(settings)

        session.commit()
        session.refresh(settings)
        return AISettingsResponse(**settings.to_dict())


@router.post("/api/ai/assist", response_model=AIAssistResponse)
async def ai_assist(request: AIAssistRequest):
    """
    AI assistance for debugging playbook executions.
    Calls Claude API to provide intelligent debugging suggestions.
    """
    try:
        # Build execution context
        context_parts = [
            f"Execution ID: {request.execution_id}",
        ]

        playbook_name = None
        current_step_index = None
        status_str = None
        step_results_list = []

        # Try to get execution context from active engines first
        from ignition_toolkit.api.app import active_engines

        engine = active_engines.get(request.execution_id)
        if engine:
            execution_state = engine.get_current_execution()
            if execution_state:
                playbook_name = execution_state.playbook_name
                current_step_index = execution_state.current_step_index
                status_str = execution_state.status.value
                step_results_list = execution_state.step_results
                logger.info(
                    f"AI Assist - Found active engine: playbook={playbook_name}, step_index={current_step_index}, status={status_str}, num_results={len(step_results_list)}"
                )
        else:
            # If not in active engines, load from database
            try:
                database = get_database()
                with database.session_scope() as session:
                    from ignition_toolkit.storage.models import ExecutionModel, StepResultModel

                    db_exec = (
                        session.query(ExecutionModel)
                        .filter(ExecutionModel.execution_id == request.execution_id)
                        .first()
                    )

                    if db_exec:
                        playbook_name = db_exec.playbook_name
                        status_str = db_exec.status

                        # Get step results from database
                        db_steps = (
                            session.query(StepResultModel)
                            .filter(StepResultModel.execution_id == db_exec.id)
                            .order_by(StepResultModel.id)
                            .all()
                        )

                        # Find the current step index (last failed or paused step)
                        current_step_index = len(db_steps) - 1 if db_steps else 0

                        # Convert to ExecutionResult objects for compatibility
                        from ignition_toolkit.playbook.models import (
                            ExecutionResult,
                            ExecutionStatus,
                        )

                        step_results_list = [
                            ExecutionResult(
                                step_id=step.step_id,
                                step_name=step.step_name,
                                status=ExecutionStatus(step.status),
                                error=step.error_message,
                                started_at=step.started_at,
                                completed_at=step.completed_at,
                            )
                            for step in db_steps
                        ]
            except Exception as e:
                logger.warning(f"AI Assist: Failed to load execution from database: {e}")

        # If we have playbook info, build the context
        if playbook_name:
            context_parts.append(f"Playbook: {playbook_name}")
            context_parts.append(f"Status: {status_str}")

            # Show current step info from execution results
            if step_results_list and len(step_results_list) > 0:
                last_result = step_results_list[-1]
                context_parts.append(
                    f"Current Step: {last_result.step_name} (ID: {last_result.step_id})"
                )
                context_parts.append(f"Step Status: {last_result.status.value}")
                if last_result.error:
                    context_parts.append(f"Error: {last_result.error}")

            # Try to load the playbook to get additional step details
            from ignition_toolkit.playbook.loader import PlaybookLoader

            playbooks_dir = get_playbooks_dir()
            loader = PlaybookLoader()
            playbook = None
            for yaml_file in playbooks_dir.rglob("*.yaml"):
                try:
                    temp_playbook = loader.load_from_file(yaml_file)
                    if temp_playbook.name == playbook_name:
                        playbook = temp_playbook
                        break
                except:
                    continue

            # If we have the playbook and current step index, add parameter details
            if (
                playbook
                and current_step_index is not None
                and current_step_index < len(playbook.steps)
            ):
                current_step = playbook.steps[current_step_index]
                context_parts.append(f"Step Type: {current_step.type}")
                if hasattr(current_step, "parameters"):
                    context_parts.append(f"Step Parameters: {current_step.parameters}")
        else:
            # No execution found at all
            context_parts.append("Note: Execution not found in active engines or database")
            if request.current_step_id:
                context_parts.append(f"Step mentioned: {request.current_step_id}")
            if request.error_context:
                context_parts.append(f"Error context: {request.error_context}")

        # Format context for AI
        execution_context = "\n".join(f"• {part}" for part in context_parts)

        # Get AI settings from database
        database = get_database()

        # Extract settings values inside session scope to avoid detached instance errors
        with database.session_scope() as session:
            from ignition_toolkit.storage.models import AISettingsModel

            # Query by credential_name if provided, otherwise get first enabled
            if request.credential_name:
                settings = (
                    session.query(AISettingsModel)
                    .filter(AISettingsModel.name == request.credential_name)
                    .first()
                )
            else:
                settings = (
                    session.query(AISettingsModel).filter(AISettingsModel.enabled == "true").first()
                )

            # Fallback to any credential if none found
            if not settings:
                settings = session.query(AISettingsModel).first()

            # Check if AI is configured and enabled
            if not settings or settings.enabled != "true" or not settings.api_key:
                return AIAssistResponse(
                    message=(
                        "⚙️ **AI is not configured**\n\n"
                        "To enable AI chat, please go to the Credentials page and configure your AI provider.\n\n"
                        "**Current Context:**\n" + execution_context + "\n\n"
                        "**Your Question:** " + request.user_message
                    ),
                    suggested_fix=None,
                    can_auto_apply=False,
                )

            # Extract all values while still in session scope
            provider = settings.provider
            api_key = settings.api_key
            api_base_url = settings.api_base_url
            model_name = settings.model_name

        # Build the prompt for the AI
        ai_prompt = (
            f"{execution_context}\n\n"
            f"User question: {request.user_message}\n\n"
            f"Please help debug this Ignition SCADA playbook automation issue. "
            f"Provide specific, actionable suggestions."
        )

        # Call AI based on provider (using extracted values, not detached object)
        try:
            if provider == "openai" or provider == "local":
                # Use OpenAI SDK (works for both OpenAI and local LLMs)
                import openai

                client = openai.OpenAI(
                    api_key=api_key, base_url=api_base_url if provider == "local" else None
                )

                response = client.chat.completions.create(
                    model=model_name or "gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful debugging assistant for Ignition SCADA playbook automation. Provide clear, actionable suggestions.",
                        },
                        {"role": "user", "content": ai_prompt},
                    ],
                    max_tokens=1024,
                )

                ai_message = response.choices[0].message.content

            elif provider == "anthropic":
                # Use Anthropic SDK
                import anthropic

                client = anthropic.Anthropic(api_key=api_key)

                response = client.messages.create(
                    model=model_name or "claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": ai_prompt}],
                )

                ai_message = response.content[0].text

            elif provider == "gemini":
                # Use Google Generative AI SDK
                import google.generativeai as genai

                genai.configure(api_key=api_key)

                model = genai.GenerativeModel(model_name or "gemini-1.5-flash")
                response = model.generate_content(ai_prompt)

                ai_message = response.text

            else:
                ai_message = f"⚠️ Unknown AI provider: {provider}. Please update your settings."

            return AIAssistResponse(message=ai_message, suggested_fix=None, can_auto_apply=False)

        except Exception as ai_error:
            logger.error(f"AI API call failed: {ai_error}")
            return AIAssistResponse(
                message=(
                    f"⚠️ **AI API Error**\n\n"
                    f"Failed to call {provider} API: {str(ai_error)}\n\n"
                    f"Please check your API key and settings in the Credentials page.\n\n"
                    f"**Current Context:**\n{execution_context}\n\n"
                    f"**Your Question:** {request.user_message}"
                ),
                suggested_fix=None,
                can_auto_apply=False,
            )

    except Exception as e:
        logger.exception(f"AI assist error: {e}")
        # Don't raise HTTP error - return helpful message instead
        return AIAssistResponse(
            message=f"⚠️ I encountered an issue collecting context, but I can still help!\n\nError: {str(e)}\n\nPlease describe your issue and I'll do my best to assist.",
            suggested_fix=None,
            can_auto_apply=False,
        )


@router.post("/api/ai/claude-code-session", response_model=ClaudeCodeSessionResponse)
async def create_claude_code_session(request: ClaudeCodeSessionRequest):
    """
    Generate a Claude Code startup command with full execution context.
    Returns a shell command that opens Claude Code with the playbook file
    and debugging context pre-loaded.
    """
    execution_id = request.execution_id

    # Get execution context
    from ignition_toolkit.api.app import active_engines

    engine = active_engines.get(execution_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Execution not found or not active")

    execution_state = engine.get_current_execution()
    if not execution_state:
        raise HTTPException(status_code=404, detail="Execution state not available")

    # Find playbook path
    playbook_name = execution_state.playbook_name
    playbooks_dir = get_playbooks_dir()
    playbook_path = None

    for yaml_file in playbooks_dir.rglob("*.yaml"):
        try:
            with open(yaml_file) as f:
                playbook_data = yaml.safe_load(f)
                if playbook_data and playbook_data.get("name") == playbook_name:
                    playbook_path = str(yaml_file.absolute())
                    break
        except Exception:
            continue

    if not playbook_path:
        raise HTTPException(
            status_code=404, detail=f"Playbook file not found for '{playbook_name}'"
        )

    # Build context message with current step, error, status
    context_parts = [
        "# Playbook Execution Debug Session",
        "",
        f"**Execution ID:** {execution_id}",
        f"**Playbook:** {playbook_name}",
        f"**Status:** {execution_state.status.value}",
        f"**Current Step:** {execution_state.current_step_index + 1 if execution_state.current_step_index is not None else 'N/A'}",
        "",
    ]

    # Add step results
    if execution_state.step_results:
        context_parts.append("## Step Results:")
        for idx, result in enumerate(execution_state.step_results, 1):
            status_emoji = "✅" if result.get("status") == "success" else "❌"
            context_parts.append(
                f"{status_emoji} **Step {idx}:** {result.get('step_name', 'Unknown')}"
            )
            if result.get("error"):
                context_parts.append(f"   Error: {result['error']}")
            if result.get("output"):
                context_parts.append(f"   Output: {result['output']}")
        context_parts.append("")

    # Add parameters
    if execution_state.parameters:
        context_parts.append("## Parameters:")
        for key, value in execution_state.parameters.items():
            # Mask sensitive values
            display_value = (
                "***"
                if any(
                    sensitive in key.lower() for sensitive in ["password", "token", "key", "secret"]
                )
                else value
            )
            context_parts.append(f"- {key}: {display_value}")
        context_parts.append("")

    context_message = "\n".join(context_parts)

    # Generate Claude Code command
    # Escape quotes in context message for shell
    escaped_context = context_message.replace('"', '\\"').replace("$", "\\$")

    command = f'''claude-code -p "{playbook_path}" -m "{escaped_context}

You are debugging a paused Ignition Automation Toolkit playbook execution. The playbook YAML file is open for editing.

**Your Task:**
1. Review the execution context above
2. Identify why the playbook failed or is paused
3. Suggest fixes to the playbook YAML
4. With user approval, edit the playbook to resolve issues

**Guidelines:**
- The playbook uses YAML syntax (see docs/playbook_syntax.md)
- Credentials use {{ credential.name }} references
- Parameters use {{ parameter.name }} references
- Browser steps use CSS selectors
- All changes require user approval before applying"'''

    return ClaudeCodeSessionResponse(
        command=command,
        playbook_path=playbook_path,
        execution_id=execution_id,
        context_message=context_message,
    )
