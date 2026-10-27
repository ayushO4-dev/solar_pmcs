"""
Solar Panel Tracking System REST API
=====================================

Run from backend/:  uv run uvicorn app.main:app --reload
Interactive docs:   http://localhost:8000/docs

SENSOR ENDPOINTS:
  GET    /api/sensor/realtime                 - Latest sensor reading
  GET    /api/sensor/recent?limit=20          - Recent readings, oldest first
  GET    /api/sensor/offsets                  - Sensor calibration offsets
  POST   /api/sensor/offsets                  - Update sensor offsets
  GET    /api/sensor/readings/export          - Download all readings as CSV

PANEL CONTROL ENDPOINTS:
  GET    /api/panel/state                     - Realtime/expected angles, range and offset
  GET    /api/panel/angle                     - Realtime angles
  POST   /api/panel/angle                     - Set target angles {yaw, roll}
  GET    /api/panel/expected                  - Target angles
  GET    /api/panel/range                     - Allowed yaw/roll range
  GET    /api/panel/offset                    - Angular calibration offset
  POST   /api/panel/offset                    - Update angular offset {yaw, roll}
  GET    /api/panel/curves                    - Time-of-day angle schedule
  PUT    /api/panel/curves                    - Replace the schedule
  POST   /api/panel/curves                    - Add/replace one schedule point
  DELETE /api/panel/curves/{HH:MM}            - Delete one schedule point
  POST   /api/panel/curves/apply              - Move to the current schedule point
  GET    /api/panel/optimal                   - Today's optimal angles from sun position

SYSTEM ENDPOINTS:
  GET    /api/system/tracking                 - Tracking loop status
  POST   /api/system/tracking?enable=bool     - Enable/disable tracking
  GET    /api/system/status                   - System status and uptime
  POST   /api/system/status                   - Set status (active, sleep, reboot, shutdown)

CONFIG ENDPOINTS:
  GET    /api/config/api-server               - API server URL
  POST   /api/config/api-server               - Update API server URL
"""

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import db, sampler, tracking
from .config import settings
from .routers import panel, sensor, system


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.pool.open(wait=True, timeout=10)
    tracking.start()
    sampler_task = asyncio.create_task(sampler.run())
    print("[Startup] Panel tracking and sensor sampling started")

    yield

    sampler_task.cancel()
    await tracking.stop()
    await db.pool.close()
    print("[Shutdown] Background tasks stopped")


app = FastAPI(title="Solar Panel Tracking API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sensor.router)
app.include_router(panel.router)
app.include_router(system.router)


@app.get("/api")
async def root():
    """API root with basic info"""
    return {
        "name": "Solar Panel Tracking API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "sensor": "/api/sensor/*",
            "panel": "/api/panel/*",
            "system": "/api/system/*",
            "config": "/api/config/*",
        },
    }


# Serve the built dashboard from the same origin when it exists
if os.path.isdir(settings.frontend_dist):
    app.mount("/", StaticFiles(directory=settings.frontend_dist, html=True), name="frontend")
