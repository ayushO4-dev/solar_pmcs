import datetime as dt
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException

from .. import db
from ..config import settings
from ..schemas import Angles, CurvePoint, OptimalPoint, PanelRange, PanelState
from ..solar import generate_optimal_angles

router = APIRouter(prefix="/api/panel", tags=["panel"])


async def _get_state() -> dict:
    state = await db.fetch_one("SELECT * FROM panel_state WHERE id = 1")
    if not state:
        raise HTTPException(status_code=500, detail="Panel state row is missing")
    return state


def _range(state: dict) -> PanelRange:
    return PanelRange(yaw=(state["yaw_min"], state["yaw_max"]), roll=(state["roll_min"], state["roll_max"]))


async def set_expected(yaw: float, roll: float) -> Angles:
    """Set the target angles the tracking loop moves the panel towards"""
    state = await _get_state()
    if not (state["yaw_min"] <= yaw <= state["yaw_max"]) or not (state["roll_min"] <= roll <= state["roll_max"]):
        raise HTTPException(
            status_code=400,
            detail=f"Angles outside panel range: yaw {state['yaw_min']:g}-{state['yaw_max']:g}°, "
                   f"roll {state['roll_min']:g}-{state['roll_max']:g}°",
        )

    await db.execute(
        "UPDATE panel_state SET expected_yaw = %s, expected_roll = %s, updated_at = now() WHERE id = 1",
        (yaw, roll),
    )
    return Angles(yaw=yaw, roll=roll)


async def wake() -> None:
    """An explicit move command takes the system out of sleep mode"""
    await db.execute(
        "UPDATE system_state SET status = 'active', updated_at = now() WHERE id = 1 AND status = 'sleep'"
    )


@router.get("/state", response_model=PanelState)
async def get_panel_state():
    """Get realtime and expected angles, range and offset in one call"""
    state = await _get_state()
    return PanelState(
        realtime=Angles(yaw=state["realtime_yaw"], roll=state["realtime_roll"]),
        expected=Angles(yaw=state["expected_yaw"], roll=state["expected_roll"]),
        range=_range(state),
        offset=Angles(yaw=state["offset_yaw"], roll=state["offset_roll"]),
    )


@router.get("/angle", response_model=Angles)
async def get_panel_angle():
    """Get the panel's current (realtime) angles"""
    state = await _get_state()
    return Angles(yaw=state["realtime_yaw"], roll=state["realtime_roll"])


@router.get("/expected", response_model=Angles)
async def get_panel_expected():
    """Get the angles the panel is moving towards"""
    state = await _get_state()
    return Angles(yaw=state["expected_yaw"], roll=state["expected_roll"])


@router.post("/angle", response_model=Angles)
async def update_panel_angle(angles: Angles):
    """Manually set the target angles"""
    result = await set_expected(angles.yaw, angles.roll)
    await wake()
    return result


@router.get("/range", response_model=PanelRange)
async def get_panel_range():
    return _range(await _get_state())


@router.get("/offset", response_model=Angles)
async def get_panel_offset():
    """Get the angular calibration offset between panel angles and motor angles"""
    state = await _get_state()
    return Angles(yaw=state["offset_yaw"], roll=state["offset_roll"])


@router.post("/offset", response_model=Angles)
async def update_panel_offset(offset: Angles):
    """Update the angular calibration offset"""
    await db.execute(
        "UPDATE panel_state SET offset_yaw = %s, offset_roll = %s, updated_at = now() WHERE id = 1",
        (offset.yaw, offset.roll),
    )
    return offset


# ==================== CURVES ====================

def _curve_point(row: dict) -> CurvePoint:
    return CurvePoint(time=row["slot_time"].strftime("%H:%M"), yaw=row["yaw"], roll=row["roll"])


@router.get("/curves", response_model=list[CurvePoint])
async def get_curves():
    """Get the time-of-day angle schedule"""
    rows = await db.fetch_all("SELECT slot_time, yaw, roll FROM angle_curves ORDER BY slot_time")
    return [_curve_point(row) for row in rows]


@router.put("/curves", response_model=list[CurvePoint])
async def replace_curves(points: list[CurvePoint]):
    """Replace the whole schedule (e.g. with the optimal curve)"""
    async with db.pool.connection() as conn:
        async with conn.transaction():
            await conn.execute("DELETE FROM angle_curves")
            for p in points:
                await conn.execute(
                    "INSERT INTO angle_curves (slot_time, yaw, roll) VALUES (%s, %s, %s)",
                    (dt.time.fromisoformat(p.time), p.yaw, p.roll),
                )
    return sorted(points, key=lambda p: p.time)


@router.post("/curves", response_model=CurvePoint)
async def upsert_curve_point(point: CurvePoint):
    """Add a point to the schedule, replacing any point at the same time"""
    await db.execute(
        """INSERT INTO angle_curves (slot_time, yaw, roll) VALUES (%s, %s, %s)
           ON CONFLICT (slot_time) DO UPDATE SET yaw = EXCLUDED.yaw, roll = EXCLUDED.roll""",
        (dt.time.fromisoformat(point.time), point.yaw, point.roll),
    )
    return point


@router.delete("/curves/{time}", status_code=204)
async def delete_curve_point(time: str):
    try:
        slot = dt.time.fromisoformat(time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Time must be HH:MM")
    if not await db.execute("DELETE FROM angle_curves WHERE slot_time = %s", (slot,)):
        raise HTTPException(status_code=404, detail="No curve point at that time")


@router.post("/curves/apply", response_model=Angles)
async def apply_current_curve():
    """Move the panel to the latest schedule point at or before the current time"""
    now = dt.datetime.now(ZoneInfo(settings.timezone)).time()
    row = await db.fetch_one(
        "SELECT slot_time, yaw, roll FROM angle_curves WHERE slot_time <= %s ORDER BY slot_time DESC LIMIT 1",
        (now,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="No curve point at or before the current time")

    # Schedule points (e.g. from the optimal curve) can fall outside the mechanical range
    state = await _get_state()
    yaw = max(state["yaw_min"], min(state["yaw_max"], row["yaw"]))
    roll = max(state["roll_min"], min(state["roll_max"], row["roll"]))
    result = await set_expected(yaw, roll)
    await wake()
    return result


@router.get("/optimal", response_model=list[OptimalPoint])
async def get_optimal_angles():
    """Get recommended angles for today from the solar position calculation"""
    try:
        results = generate_optimal_angles(
            dt.datetime.now(ZoneInfo(settings.timezone)), settings.op_start, settings.op_span_hours
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate angles: {e}")
    return [OptimalPoint(time=r["time"], yaw=r["yaw"], roll=r["roll"], invert=r["invert"]) for r in results]
