"""
Ignition Automation Toolkit

Lightweight, transferable automation platform for Ignition SCADA Gateway operations.
"""

__version__ = (
    "3.6.0"  # Updated: 2025-10-28 - Terminology fix (unverified), nested playbook execution (gateway_login in reset_trial)
)
__build_date__ = "2025-10-28"
__phases_complete__ = "8/8 (100%)"
__author__ = "Nigel G"
__license__ = "MIT"

from ignition_toolkit.gateway.client import GatewayClient
from ignition_toolkit.playbook.engine import PlaybookEngine
from ignition_toolkit.playbook.models import ExecutionState, Playbook, PlaybookStep

__all__ = [
    "GatewayClient",
    "PlaybookEngine",
    "Playbook",
    "PlaybookStep",
    "ExecutionState",
]
