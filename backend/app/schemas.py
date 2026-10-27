"""Request and response models."""

import datetime as dt
from typing import Annotated, Literal

from pydantic import BaseModel, Field

# "HH:MM", 24-hour clock
TimeOfDay = Annotated[str, Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")]


class SensorReading(BaseModel):
    recorded_at: dt.datetime
    voltage: float | None
    current: float | None
    wattage: float | None
    temperature: float | None
    humidity: float | None


class SensorOffsets(BaseModel):
    voltage: float = 0
    current: float = 0
    wattage: float = 0
    temperature: float = 0
    humidity: float = 0


class Angles(BaseModel):
    yaw: float
    roll: float


class PanelRange(BaseModel):
    yaw: tuple[float, float]
    roll: tuple[float, float]


class PanelState(BaseModel):
    realtime: Angles
    expected: Angles
    range: PanelRange
    offset: Angles


class CurvePoint(BaseModel):
    time: TimeOfDay
    yaw: float
    roll: float


class OptimalPoint(CurvePoint):
    invert: bool


class TrackingStatus(BaseModel):
    enabled: bool
    running: bool


class SystemStatus(BaseModel):
    status: str
    uptime_seconds: int
    firmware_version: str


class StatusUpdate(BaseModel):
    status: Literal["active", "sleep", "reboot", "shutdown"]


class ApiServerConfig(BaseModel):
    value: str
