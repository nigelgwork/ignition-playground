"""
Integration tests for playbook execution
"""

import tempfile
from pathlib import Path

import pytest

from ignition_toolkit.credentials import Credential, CredentialVault
from ignition_toolkit.playbook.engine import PlaybookEngine
from ignition_toolkit.playbook.loader import PlaybookLoader
from ignition_toolkit.playbook.models import ExecutionStatus
from ignition_toolkit.storage import get_database


@pytest.fixture
def temp_dir():
    """Create temporary directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def vault(temp_dir):
    """Create credential vault"""
    vault = CredentialVault(vault_path=temp_dir / "vault")
    vault.save_credential(Credential(name="test_cred", username="testuser", password="testpass"))
    return vault


@pytest.fixture
def database(temp_dir):
    """Create test database"""
    db_path = temp_dir / "test.db"
    return get_database(database_path=db_path)


@pytest.fixture
def simple_playbook_yaml():
    """Simple playbook for testing"""
    return """
name: "Integration Test"
version: "1.0"

parameters:
  - name: message
    type: string
    required: false
    default: "Hello World"

steps:
  - id: log1
    name: "Log Start"
    type: utility.log
    parameters:
      message: "Starting test"
      level: "info"

  - id: sleep
    name: "Short Sleep"
    type: utility.sleep
    parameters:
      seconds: 0.1

  - id: set_var
    name: "Set Variable"
    type: utility.set_variable
    parameters:
      name: "test_var"
      value: "test_value"

  - id: log2
    name: "Log End"
    type: utility.log
    parameters:
      message: "{{ parameter.message }}"
      level: "info"
"""


@pytest.mark.asyncio
async def test_simple_playbook_execution(simple_playbook_yaml, vault, database):
    """Test executing a simple playbook"""
    # Load playbook
    loader = PlaybookLoader()
    playbook = loader.load_from_string(simple_playbook_yaml)

    # Create engine
    engine = PlaybookEngine(credential_vault=vault, database=database)

    # Execute
    parameters = {"message": "Test Complete"}
    execution_state = await engine.execute_playbook(playbook, parameters)

    # Verify
    assert execution_state.status == ExecutionStatus.COMPLETED
    assert len(execution_state.step_results) == 4
    assert execution_state.error is None

    # Check all steps completed
    for result in execution_state.step_results:
        assert result.status.value == "completed"


@pytest.mark.asyncio
async def test_playbook_with_failure(vault, database):
    """Test playbook that fails"""
    yaml_content = """
name: "Failure Test"
version: "1.0"

steps:
  - id: step1
    name: "Will Fail"
    type: utility.log
    parameters:
      message: "Before failure"

  - id: step2
    name: "Bad Step"
    type: gateway.login
    parameters:
      username: "admin"
    timeout: 1
    on_failure: abort
"""

    loader = PlaybookLoader()
    playbook = loader.load_from_string(yaml_content)

    engine = PlaybookEngine(credential_vault=vault, database=database)

    execution_state = await engine.execute_playbook(playbook, {})

    # Should fail on second step (no gateway client)
    assert execution_state.status == ExecutionStatus.FAILED
    assert execution_state.error is not None


@pytest.mark.asyncio
async def test_playbook_with_retry(vault, database):
    """Test retry functionality"""
    yaml_content = """
name: "Retry Test"
version: "1.0"

steps:
  - id: step1
    name: "Will Retry"
    type: gateway.ping
    timeout: 1
    retry_count: 2
    retry_delay: 0.1
    on_failure: continue

  - id: step2
    name: "Continue After Failure"
    type: utility.log
    parameters:
      message: "Continued after failure"
"""

    loader = PlaybookLoader()
    playbook = loader.load_from_string(yaml_content)

    engine = PlaybookEngine(credential_vault=vault, database=database)

    execution_state = await engine.execute_playbook(playbook, {})

    # First step should fail but continue
    assert len(execution_state.step_results) == 2
    assert execution_state.step_results[0].status.value == "failed"
    assert execution_state.step_results[0].retry_count == 2  # Retried twice
    assert execution_state.step_results[1].status.value == "completed"


@pytest.mark.asyncio
async def test_parameter_resolution_in_execution(vault, database):
    """Test parameter resolution during execution"""
    yaml_content = """
name: "Parameter Test"
version: "1.0"

parameters:
  - name: test_message
    type: string
    required: true

steps:
  - id: log
    name: "Log Message"
    type: utility.log
    parameters:
      message: "Message: {{ parameter.test_message }}"
"""

    loader = PlaybookLoader()
    playbook = loader.load_from_string(yaml_content)

    engine = PlaybookEngine(credential_vault=vault, database=database)

    execution_state = await engine.execute_playbook(
        playbook, {"test_message": "Resolved Successfully"}
    )

    assert execution_state.status == ExecutionStatus.COMPLETED


@pytest.mark.asyncio
async def test_execution_callback(simple_playbook_yaml, vault, database):
    """Test execution update callbacks"""
    loader = PlaybookLoader()
    playbook = loader.load_from_string(simple_playbook_yaml)

    engine = PlaybookEngine(credential_vault=vault, database=database)

    updates = []

    def callback(state):
        updates.append(
            {"step_index": state.current_step_index, "step_count": len(state.step_results)}
        )

    engine.set_update_callback(callback)

    await engine.execute_playbook(playbook, {})

    # Should have received updates
    assert len(updates) > 0


@pytest.mark.asyncio
async def test_database_tracking(simple_playbook_yaml, vault, database):
    """Test that execution is saved to database"""
    loader = PlaybookLoader()
    playbook = loader.load_from_string(simple_playbook_yaml)

    engine = PlaybookEngine(credential_vault=vault, database=database)

    execution_state = await engine.execute_playbook(playbook, {})

    # Check database
    with database.session_scope() as session:
        from ignition_toolkit.storage.models import ExecutionModel, StepResultModel

        executions = session.query(ExecutionModel).all()
        assert len(executions) == 1

        execution = executions[0]
        assert execution.playbook_name == "Integration Test"
        assert execution.status == "completed"

        # Check step results
        steps = session.query(StepResultModel).filter_by(execution_id=execution.id).all()
        assert len(steps) == 4
