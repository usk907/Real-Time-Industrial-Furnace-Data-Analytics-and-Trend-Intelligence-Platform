"""
IEIP Master API Router
Aggregates all domain-specific sub-routers into a unified API surface and maintains backward-compatible re-exports.
"""
from fastapi import APIRouter

# Import sub-routers
from backend.app.routers.auth import router as auth_router
from backend.app.routers.plants import router as plants_router
from backend.app.routers.dashboard import router as dashboard_router
from backend.app.routers.telemetry import router as telemetry_router
from backend.app.routers.consumption import router as consumption_router
from backend.app.routers.analytics import router as analytics_router
from backend.app.routers.alarms import router as alarms_router
from backend.app.routers.reports import router as reports_router
from backend.app.routers.settings import router as settings_router
from backend.app.routers.ai import router as ai_router

# Import services for backward compatibility re-exports
from backend.app.services.kpi_engine import (
    frozen_detection_cache,
    log_audit,
    add_notification,
    get_db_setting,
    check_and_trigger_alarms,
    check_frozen_sensor,
    calculate_kpis,
    compute_moving_regression_forecast
)
from backend.app.services.ai_copilot import (
    ChatMessage,
    ChatPayload,
    AIQueryPayload,
    process_copilot_chat,
    execute_ai_query
)

# Root aggregated router
router = APIRouter()

# Mount all domain sub-routers
router.include_router(auth_router)
router.include_router(plants_router)
router.include_router(dashboard_router)
router.include_router(telemetry_router)
router.include_router(consumption_router)
router.include_router(analytics_router)
router.include_router(alarms_router)
router.include_router(reports_router)
router.include_router(settings_router)
router.include_router(ai_router)

# Aliases for backward compatibility
api_router = router

__all__ = [
    "router",
    "api_router",
    "frozen_detection_cache",
    "log_audit",
    "add_notification",
    "get_db_setting",
    "check_and_trigger_alarms",
    "check_frozen_sensor",
    "calculate_kpis",
    "compute_moving_regression_forecast",
    "ChatMessage",
    "ChatPayload",
    "AIQueryPayload",
    "process_copilot_chat",
    "execute_ai_query"
]
