"""
Ignition Automation Toolkit

Lightweight, transferable automation platform for Ignition SCADA Gateway operations.
"""

__version__ = "5.1.1"  # Updated: 2025-11-26 - Playbook library, UI fixes, duplicate naming
__build_date__ = "2025-11-26"
__phases_complete__ = "10/10 (100%) + Plugin Architecture Complete"
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
