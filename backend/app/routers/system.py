from fastapi import APIRouter

from .. import db, tracking
from ..schemas import ApiServerConfig, StatusUpdate, SystemStatus, TrackingStatus
from .panel import set_expected

router = APIRouter(tags=["system"])


def _uptime_seconds() -> int:
    try:
        with open("/proc/uptime") as f:
            return int(float(f.readline().split()[0]))
    except OSError:
        return 0


@router.get("/api/system/tracking", response_model=TrackingStatus)
async def get_tracking_status():
    """Get panel tracking background task status"""
    return TrackingStatus(enabled=tracking.enabled, running=tracking.is_running())


@router.post("/api/system/tracking", response_model=TrackingStatus)
async def toggle_tracking(enable: bool):
    """Enable or disable panel tracking"""
    if enable:
        tracking.start()
    else:
        await tracking.stop()
    return TrackingStatus(enabled=tracking.enabled, running=tracking.is_running())


@router.get("/api/system/status", response_model=SystemStatus)
async def get_system_status():
    """Get system status and host uptime"""
    row = await db.fetch_one("SELECT status, firmware_version FROM system_state WHERE id = 1")
    return SystemStatus(
        status=row["status"] if row else "unknown",
        uptime_seconds=_uptime_seconds(),
        firmware_version=row["firmware_version"] if row else "unknown",
    )


@router.post("/api/system/status", response_model=SystemStatus)
async def update_system_status(update: StatusUpdate):
    """
    Record a status change. "sleep" also stows the panel at its minimum angles;
    the next manual move or applied curve point sets the status back to "active".
    Reboot and shutdown are recorded only; they do not act on the host yet.
    """
    if update.status == "sleep":
        state = await db.fetch_one("SELECT yaw_min, roll_min FROM panel_state WHERE id = 1")
        await set_expected(state["yaw_min"], state["roll_min"])

    await db.execute(
        "UPDATE system_state SET status = %s, updated_at = now() WHERE id = 1", (update.status,)
    )
    return await get_system_status()


# ==================== CONFIG ====================

@router.get("/api/config/api-server", response_model=ApiServerConfig)
async def get_api_server():
    """Get API server URL configuration"""
    row = await db.fetch_one("SELECT value FROM system_config WHERE key = 'api_server'")
    return ApiServerConfig(value=row["value"] if row else "")


@router.post("/api/config/api-server", response_model=ApiServerConfig)
async def update_api_server(config: ApiServerConfig):
    """Update API server URL"""
    await db.execute(
        """INSERT INTO system_config (key, value) VALUES ('api_server', %s)
           ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now()""",
        (config.value,),
    )
    return config
