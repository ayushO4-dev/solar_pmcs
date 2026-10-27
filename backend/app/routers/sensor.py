import csv
import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from .. import db
from ..hardware.sensors import READING_KEYS
from ..schemas import SensorOffsets, SensorReading

router = APIRouter(prefix="/api/sensor", tags=["sensor"])

READING_COLUMNS = "recorded_at, " + ", ".join(READING_KEYS)


@router.get("/realtime", response_model=SensorReading)
async def get_latest_reading():
    """Get the most recent sensor reading"""
    row = await db.fetch_one(
        f"SELECT {READING_COLUMNS} FROM sensor_readings ORDER BY recorded_at DESC LIMIT 1"
    )
    if not row:
        raise HTTPException(status_code=404, detail="No readings found")
    return row


@router.get("/recent", response_model=list[SensorReading])
async def get_recent_readings(limit: int = Query(20, ge=1, le=1000)):
    """Get the most recent readings, oldest first"""
    rows = await db.fetch_all(
        f"SELECT {READING_COLUMNS} FROM sensor_readings ORDER BY recorded_at DESC LIMIT %s",
        (limit,),
    )
    return rows[::-1]


@router.get("/offsets", response_model=SensorOffsets)
async def get_sensor_offsets():
    """Get sensor calibration offsets"""
    rows = await db.fetch_all("SELECT sensor, value FROM sensor_offsets")
    return {row["sensor"]: row["value"] for row in rows}


@router.post("/offsets", response_model=SensorOffsets)
async def update_sensor_offsets(offsets: SensorOffsets):
    """Update sensor calibration offsets; applied to readings sampled from now on"""
    async with db.pool.connection() as conn:
        for sensor, value in offsets.model_dump().items():
            await conn.execute(
                "UPDATE sensor_offsets SET value = %s, updated_at = now() WHERE sensor = %s",
                (value, sensor),
            )
    return offsets


@router.get("/readings/export")
async def export_readings():
    """Download all sensor readings as CSV"""
    rows = await db.fetch_all(f"SELECT {READING_COLUMNS} FROM sensor_readings ORDER BY recorded_at ASC")

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["recorded_at", *READING_KEYS])
    for row in rows:
        writer.writerow([row["recorded_at"].isoformat(), *(row[key] for key in READING_KEYS)])

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="solar_readings.csv"'},
    )
