"""
Ignition Automation Toolkit

Lightweight, transferable automation platform for Ignition SCADA Gateway operations.
"""

__version__ = "3.45.8"  # Updated: 2025-10-31 - Responsive grid: 3 cols on laptops, 4 on xl screens
__build_date__ = "2025-10-31"
__phases_complete__ = "10/10 (100%) + Complete Service Layer"
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
