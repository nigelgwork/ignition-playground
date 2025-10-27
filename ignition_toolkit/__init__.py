"""
Ignition Automation Toolkit

Lightweight, transferable automation platform for Ignition SCADA Gateway operations.
"""

__version__ = "2.3.0"  # Updated: 2025-10-27
__build_date__ = "2025-10-27"
__phases_complete__ = "8/8 (100%)"
__author__ = "Nigel G"
__license__ = "MIT"

from ignition_toolkit.gateway.client import GatewayClient
from ignition_toolkit.playbook.engine import PlaybookEngine
from ignition_toolkit.playbook.models import Playbook, PlaybookStep, ExecutionState

__all__ = [
    "GatewayClient",
    "PlaybookEngine",
    "Playbook",
    "PlaybookStep",
    "ExecutionState",
]
