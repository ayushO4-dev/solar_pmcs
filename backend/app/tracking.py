"""
Background task that moves the panel's realtime angles towards the expected angles.

Each tick steps yaw and roll by at most `tracking_step_deg`, clamped to the panel
range. Until a motor driver is wired in, this simulates the motor movement.
"""

import asyncio

from . import db
from .config import settings

_task: asyncio.Task | None = None
enabled = False


def _step(current: float, target: float, lo: float, hi: float) -> float:
    target = max(lo, min(hi, target))
    diff = target - current
    if abs(diff) <= 0.1:  # Threshold to avoid micro-adjustments
        return current
    step = min(settings.tracking_step_deg, abs(diff))
    return round(max(lo, min(hi, current + step if diff > 0 else current - step)), 2)


async def _tick() -> None:
    state = await db.fetch_one("SELECT * FROM panel_state WHERE id = 1")
    if not state:
        return

    yaw = _step(state["realtime_yaw"], state["expected_yaw"], state["yaw_min"], state["yaw_max"])
    roll = _step(state["realtime_roll"], state["expected_roll"], state["roll_min"], state["roll_max"])

    if (yaw, roll) != (state["realtime_yaw"], state["realtime_roll"]):
        await db.execute(
            "UPDATE panel_state SET realtime_yaw = %s, realtime_roll = %s, updated_at = now() WHERE id = 1",
            (yaw, roll),
        )


async def _loop() -> None:
    while enabled:
        try:
            await _tick()
        except Exception as e:
            print(f"[Tracking Error] {e}")
        await asyncio.sleep(settings.tracking_interval_s)


def is_running() -> bool:
    return _task is not None and not _task.done()


def start() -> None:
    global _task, enabled
    enabled = True
    if not is_running():
        _task = asyncio.create_task(_loop())


async def stop() -> None:
    global enabled
    enabled = False
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
