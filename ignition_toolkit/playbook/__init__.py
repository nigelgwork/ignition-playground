"""
Playbook execution engine for Ignition Gateway automation

This module provides:
- YAML-based playbook definitions
- Parameter resolution with credential support
- Step-by-step execution with pause/resume/skip
- Execution state tracking
"""

from ignition_toolkit.playbook.models import (
    Playbook,
    PlaybookStep,
    PlaybookParameter,
    ParameterType,
    StepType,
    ExecutionState,
    ExecutionStatus,
)
from ignition_toolkit.playbook.loader import PlaybookLoader
from ignition_toolkit.playbook.engine import PlaybookEngine
from ignition_toolkit.playbook.exceptions import (
    PlaybookError,
    PlaybookLoadError,
    PlaybookValidationError,
    PlaybookExecutionError,
    StepExecutionError,
)

__all__ = [
    "Playbook",
    "PlaybookStep",
    "PlaybookParameter",
    "ParameterType",
    "StepType",
    "ExecutionState",
    "ExecutionStatus",
    "PlaybookLoader",
    "PlaybookEngine",
    "PlaybookError",
    "PlaybookLoadError",
    "PlaybookValidationError",
    "PlaybookExecutionError",
    "StepExecutionError",
]
