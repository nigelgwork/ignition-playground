"""
Tests for playbook loader
"""

import tempfile
from pathlib import Path

import pytest

from ignition_toolkit.playbook.exceptions import PlaybookLoadError, PlaybookValidationError
from ignition_toolkit.playbook.loader import PlaybookLoader
from ignition_toolkit.playbook.models import OnFailureAction, ParameterType, StepType


@pytest.fixture
def temp_dir():
    """Create temporary directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def simple_playbook_yaml():
    """Simple valid playbook YAML"""
    return """
name: "Test Playbook"
version: "1.0"
description: "Test description"

parameters:
  - name: test_param
    type: string
    required: true

steps:
  - id: step1
    name: "Test Step"
    type: utility.log
    parameters:
      message: "Hello"
"""


def test_load_from_string(simple_playbook_yaml):
    """Test loading playbook from string"""
    loader = PlaybookLoader()
    playbook = loader.load_from_string(simple_playbook_yaml)

    assert playbook.name == "Test Playbook"
    assert playbook.version == "1.0"
    assert playbook.description == "Test description"
    assert len(playbook.parameters) == 1
    assert len(playbook.steps) == 1


def test_load_from_file(temp_dir, simple_playbook_yaml):
    """Test loading playbook from file"""
    playbook_file = temp_dir / "test.yaml"
    playbook_file.write_text(simple_playbook_yaml)

    loader = PlaybookLoader()
    playbook = loader.load_from_file(playbook_file)

    assert playbook.name == "Test Playbook"


def test_save_to_file(temp_dir, simple_playbook_yaml):
    """Test saving playbook to file"""
    loader = PlaybookLoader()
    playbook = loader.load_from_string(simple_playbook_yaml)

    output_file = temp_dir / "output.yaml"
    loader.save_to_file(playbook, output_file)

    assert output_file.exists()

    # Load it back
    loaded = loader.load_from_file(output_file)
    assert loaded.name == playbook.name


def test_parameter_parsing():
    """Test parameter parsing"""
    yaml_content = """
name: "Test"
version: "1.0"

parameters:
  - name: url
    type: string
    required: true
    description: "Gateway URL"

  - name: credential
    type: credential
    required: false
    default: "admin"

steps:
  - id: step1
    name: "Step"
    type: utility.log
    parameters:
      message: "test"
"""

    loader = PlaybookLoader()
    playbook = loader.load_from_string(yaml_content)

    assert len(playbook.parameters) == 2

    param1 = playbook.parameters[0]
    assert param1.name == "url"
    assert param1.type == ParameterType.STRING
    assert param1.required is True

    param2 = playbook.parameters[1]
    assert param2.name == "credential"
    assert param2.type == ParameterType.CREDENTIAL
    assert param2.required is False


def test_step_parsing():
    """Test step parsing"""
    yaml_content = """
name: "Test"
version: "1.0"

steps:
  - id: login
    name: "Login"
    type: gateway.login
    parameters:
      username: "admin"
      password: "pass"
    timeout: 60
    retry_count: 3
    retry_delay: 10
    on_failure: continue
"""

    loader = PlaybookLoader()
    playbook = loader.load_from_string(yaml_content)

    step = playbook.steps[0]
    assert step.id == "login"
    assert step.name == "Login"
    assert step.type == StepType.GATEWAY_LOGIN
    assert step.timeout == 60
    assert step.retry_count == 3
    assert step.retry_delay == 10
    assert step.on_failure == OnFailureAction.CONTINUE


def test_missing_name():
    """Test validation with missing name"""
    yaml_content = """
version: "1.0"
steps:
  - id: step1
    name: "Step"
    type: utility.log
"""

    loader = PlaybookLoader()
    with pytest.raises(PlaybookValidationError, match="must have 'name'"):
        loader.load_from_string(yaml_content)


def test_missing_version():
    """Test validation with missing version"""
    yaml_content = """
name: "Test"
steps:
  - id: step1
    name: "Step"
    type: utility.log
"""

    loader = PlaybookLoader()
    with pytest.raises(PlaybookValidationError, match="must have 'version'"):
        loader.load_from_string(yaml_content)


def test_missing_steps():
    """Test validation with missing steps"""
    yaml_content = """
name: "Test"
version: "1.0"
"""

    loader = PlaybookLoader()
    with pytest.raises(PlaybookValidationError, match="must have 'steps'"):
        loader.load_from_string(yaml_content)


def test_empty_steps():
    """Test validation with empty steps"""
    yaml_content = """
name: "Test"
version: "1.0"
steps: []
"""

    loader = PlaybookLoader()
    with pytest.raises(PlaybookValidationError, match="at least one step"):
        loader.load_from_string(yaml_content)


def test_invalid_parameter_type():
    """Test validation with invalid parameter type"""
    yaml_content = """
name: "Test"
version: "1.0"

parameters:
  - name: test
    type: invalid_type

steps:
  - id: step1
    name: "Step"
    type: utility.log
"""

    loader = PlaybookLoader()
    with pytest.raises(PlaybookValidationError, match="Invalid parameter type"):
        loader.load_from_string(yaml_content)


def test_invalid_step_type():
    """Test validation with invalid step type"""
    yaml_content = """
name: "Test"
version: "1.0"

steps:
  - id: step1
    name: "Step"
    type: invalid.type
"""

    loader = PlaybookLoader()
    with pytest.raises(PlaybookValidationError, match="Invalid step type"):
        loader.load_from_string(yaml_content)


def test_duplicate_step_ids():
    """Test validation with duplicate step IDs"""
    yaml_content = """
name: "Test"
version: "1.0"

steps:
  - id: step1
    name: "Step 1"
    type: utility.log

  - id: step1
    name: "Step 2"
    type: utility.log
"""

    loader = PlaybookLoader()
    with pytest.raises(PlaybookValidationError, match="Step IDs must be unique"):
        loader.load_from_string(yaml_content)


def test_invalid_yaml():
    """Test with invalid YAML syntax"""
    invalid_yaml = """
name: "Test"
version: "1.0"
  invalid indentation
steps:
"""

    loader = PlaybookLoader()
    with pytest.raises(PlaybookLoadError, match="Invalid YAML"):
        loader.load_from_string(invalid_yaml)


def test_nonexistent_file():
    """Test loading nonexistent file"""
    loader = PlaybookLoader()
    with pytest.raises(PlaybookLoadError, match="not found"):
        loader.load_from_file(Path("/nonexistent/file.yaml"))
