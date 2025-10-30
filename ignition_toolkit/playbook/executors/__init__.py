"""
Step executors using Strategy Pattern

Each executor handles a specific domain of step types (gateway, browser, designer, etc.)
This allows for better separation of concerns and easier testing.
"""

from ignition_toolkit.playbook.executors.base import StepHandler
from ignition_toolkit.playbook.executors.gateway_executor import (
    GatewayGetHealthHandler,
    GatewayGetInfoHandler,
    GatewayGetProjectHandler,
    GatewayListModulesHandler,
    GatewayListProjectsHandler,
    GatewayLoginHandler,
    GatewayLogoutHandler,
    GatewayPingHandler,
    GatewayRestartHandler,
    GatewayUploadModuleHandler,
    GatewayWaitModuleHandler,
    GatewayWaitReadyHandler,
)
from ignition_toolkit.playbook.executors.browser_executor import (
    BrowserClickHandler,
    BrowserFillHandler,
    BrowserNavigateHandler,
    BrowserScreenshotHandler,
    BrowserVerifyHandler,
    BrowserWaitHandler,
)
from ignition_toolkit.playbook.executors.designer_executor import (
    DesignerCloseHandler,
    DesignerLaunchHandler,
    DesignerLoginHandler,
    DesignerOpenProjectHandler,
    DesignerScreenshotHandler,
    DesignerWaitHandler,
)
from ignition_toolkit.playbook.executors.playbook_executor import PlaybookRunHandler
from ignition_toolkit.playbook.executors.utility_executor import (
    UtilityLogHandler,
    UtilityPythonHandler,
    UtilitySetVariableHandler,
    UtilitySleepHandler,
)
from ignition_toolkit.playbook.executors.ai_executor import (
    AIAnalyzeHandler,
    AIGenerateHandler,
    AIValidateHandler,
)

__all__ = [
    "StepHandler",
    # Gateway
    "GatewayLoginHandler",
    "GatewayLogoutHandler",
    "GatewayPingHandler",
    "GatewayGetInfoHandler",
    "GatewayGetHealthHandler",
    "GatewayListModulesHandler",
    "GatewayUploadModuleHandler",
    "GatewayWaitModuleHandler",
    "GatewayListProjectsHandler",
    "GatewayGetProjectHandler",
    "GatewayRestartHandler",
    "GatewayWaitReadyHandler",
    # Browser
    "BrowserNavigateHandler",
    "BrowserClickHandler",
    "BrowserFillHandler",
    "BrowserScreenshotHandler",
    "BrowserWaitHandler",
    "BrowserVerifyHandler",
    # Designer
    "DesignerLaunchHandler",
    "DesignerLoginHandler",
    "DesignerOpenProjectHandler",
    "DesignerCloseHandler",
    "DesignerScreenshotHandler",
    "DesignerWaitHandler",
    # Playbook
    "PlaybookRunHandler",
    # Utility
    "UtilitySleepHandler",
    "UtilityLogHandler",
    "UtilitySetVariableHandler",
    "UtilityPythonHandler",
    # AI
    "AIGenerateHandler",
    "AIValidateHandler",
    "AIAnalyzeHandler",
]
