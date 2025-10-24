"""
Startup module - Application initialization and lifecycle management

Provides robust startup validation, health checks, and lifecycle management
for the Ignition Automation Toolkit.
"""

from ignition_toolkit.startup.health import (
    HealthStatus,
    ComponentHealth,
    SystemHealth,
    get_health_state,
    set_component_healthy,
    set_component_unhealthy,
    set_component_degraded,
)
from ignition_toolkit.startup.lifecycle import lifespan, is_dev_mode

__all__ = [
    "HealthStatus",
    "ComponentHealth",
    "SystemHealth",
    "get_health_state",
    "set_component_healthy",
    "set_component_unhealthy",
    "set_component_degraded",
    "lifespan",
    "is_dev_mode",
]
