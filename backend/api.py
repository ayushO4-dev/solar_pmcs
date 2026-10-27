"""
Solar Panel Tracking System REST API
=====================================

API Endpoints:

SENSOR ENDPOINTS:
  GET    /api/sensor/readings/latest          - Get latest sensor reading
  GET    /api/sensor/readings/recent          - Get recent readings (with limit param)
  GET    /api/sensor/offsets                  - Get sensor offset values
  POST   /api/sensor/offsets                  - Update sensor offsets
  GET    /api/sensor/readings/export          - Export all sensor readings

PANEL CONTROL ENDPOINTS:
  GET    /api/panel/position                  - Get current panel position
  POST   /api/panel/position                  - Update panel position (vertical, horizontal)
  GET    /api/panel/curves/                   - Get angle curves for time-based tracking
  GET    /api/panel/curves/update             - Get angle curves for time-based tracking

SYSTEM ENDPOINTS:
  GET    /api/system/status                   - Get system status and uptime
  POST   /api/system/status                   - Update system status

CONFIG ENDPOINTS:
  GET    /api/config/api-server               - Get API server URL
  POST   /api/config/api-server               - Update API server URL
  GET    /api/config/angular-offset           - Get angular offsets (yaw/roll)
  POST   /api/config/angular-offset           - Update angular offsets

EXTERNAL API ENDPOINTS:
  GET    /api/external/recommended-angles     - Get recommended angles from external calculation
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import datetime as dt
import sqlite3
import pytz
import os
import random
import asyncio
from contextlib import asynccontextmanager

from app.config import settings
from app.solar import generate_optimal_angles

TIMEZONE = settings.timezone


def json_op(mode: str, filename: str, data=None):
    import json5
    with open(f"data/{filename}", mode) as f:
        if data:
            json5.dump(data, f, indent=4)
        else: data = json5.load(f);
    return data

# Global flag to control the background task
tracking_task = None
tracking_enabled = True


async def panel_tracking_loop():
    """
    Background task that continuously adjusts realtime angles to match expected angles.
    Increments/decrements yaw and roll by small steps to simulate motor movement.
    """
    global tracking_enabled
    
    STEP_SIZE = 1  # Degrees per step
    UPDATE_INTERVAL = 0.5  # Seconds between updates
    
    while tracking_enabled:
        try:
            # Read current control data
            data = json_op('r', 'control.json5')
            
            if not data or data.get("busy", False):
                # Skip if system is busy or data unavailable
                await asyncio.sleep(UPDATE_INTERVAL)
                continue
            
            realtime = data.get("realtime", {"yaw": 0, "roll": 0})
            expected = data.get("expected", {"yaw": 0, "roll": 0})
            panel_range = data.get("range", {
                "yaw": [0, 180],
                "roll": [35, 145]
            })
            
            current_yaw = realtime["yaw"]
            current_roll = realtime["roll"]
            target_yaw = expected["yaw"]
            target_roll = expected["roll"]
            
            # Check if we need to move
            yaw_diff = target_yaw - current_yaw
            roll_diff = target_roll - current_roll
            
            # Apply constraints to target values
            target_yaw = max(panel_range["yaw"][0], min(panel_range["yaw"][1], target_yaw))
            target_roll = max(panel_range["roll"][0], min(panel_range["roll"][1], target_roll))
            
            updated = False
            
            # Update yaw
            if abs(yaw_diff) > 0.1:  # Threshold to avoid micro-adjustments
                if yaw_diff > 0:
                    new_yaw = min(current_yaw + STEP_SIZE, target_yaw)
                else:
                    new_yaw = max(current_yaw - STEP_SIZE, target_yaw)
                
                # Enforce range limits
                new_yaw = max(panel_range["yaw"][0], min(panel_range["yaw"][1], new_yaw))
                realtime["yaw"] = round(new_yaw, 2)
                updated = True
            
            # Update roll
            if abs(roll_diff) > 0.1:  # Threshold to avoid micro-adjustments
                if roll_diff > 0:
                    new_roll = min(current_roll + STEP_SIZE, target_roll)
                else:
                    new_roll = max(current_roll - STEP_SIZE, target_roll)
                
                # Enforce range limits
                new_roll = max(panel_range["roll"][0], min(panel_range["roll"][1], new_roll))
                realtime["roll"] = round(new_roll, 2)
                updated = True
            
            # Write back if any updates were made
            if updated:
                data["realtime"] = realtime
                json_op('w', 'control.json5', data)
            
            await asyncio.sleep(UPDATE_INTERVAL)
            
        except Exception as e:
            print(f"[Tracking Error] {e}")
            await asyncio.sleep(UPDATE_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager to start/stop background tasks
    """
    global tracking_task, tracking_enabled
    
    # Startup: Start the tracking task
    tracking_enabled = True
    tracking_task = asyncio.create_task(panel_tracking_loop())
    print("[Startup] Panel tracking background task started")
    
    yield
    
    # Shutdown: Stop the tracking task
    tracking_enabled = False
    if tracking_task:
        tracking_task.cancel()
        try:
            await tracking_task
        except asyncio.CancelledError:
            pass
    print("[Shutdown] Panel tracking background task stopped")


app = FastAPI(title="Solar Panel Tracking API", version="1.0.0", lifespan=lifespan) #type: ignore

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class SensorReading(BaseModel):
    voltage: Optional[float] = None
    wattage: Optional[float] = None
    ampere: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    timestamp: str

class SystemStatus(BaseModel):
    status: str
    uptime_seconds: int
    firmware_version: str = "1.0.0"

class PanelPosition(BaseModel):
    id: str = "panel_1"
    vertical_angle: float
    horizontal_angle: float
    timestamp: str

class PanelPositionUpdate(BaseModel):
    vertical_angle: float = Field(..., ge=0, le=180)
    horizontal_angle: float = Field(..., ge=0, le=180)

class AngleCurve(BaseModel):
    time: float  # Decimal hours
    yaw: float
    roll: float

class CurveBatchUpdate(BaseModel):
    type: str  # "yaw" or "roll"
    curves: List[AngleCurve]

class SensorOffsets(BaseModel):
    offsets: Dict[str, float]

class AngularOffset(BaseModel):
    yaw: float
    roll: float

class ApiServerConfig(BaseModel):
    value: str

class StatusUpdate(BaseModel):
    status: str


# Mount static files (for assets like CSS, JS)
if os.path.exists("assets"):
    app.mount("/assets", StaticFiles(directory="assets"), name="assets")

@app.get("/")
async def serve_index():
    """Serve the main index.html file"""
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    else:
        return {
            "message": "index.html not found",
            "api_docs": "/docs",
            "api_info": "/api"
        }

# Helper functions
def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect("data/sensor_readings.db")
    conn.row_factory = sqlite3.Row
    return conn


# ==================== SENSOR ENDPOINTS ====================

@app.get("/api/sensor/realtime")
async def get_reading():
    """Get the most recent sensor reading from database"""
    
    # conn = get_db_connection()
    # cursor = conn.cursor()
    
    # cursor.execute("""
    #     SELECT datetime, voltage, current, wattage, temp, humidity
    #     FROM readings
    #     ORDER BY datetime DESC
    #     LIMIT 1
    # """)
    
    # row = cursor.fetchone()
    # conn.close()
    
    # if not row:
    #     raise HTTPException(status_code=404, detail="No readings found")
    
    return {
        "timestamp":f"{dt.datetime}",
        "voltage": round(random.uniform(10,12), 2),
        "wattage": round(random.uniform(15,20), 2),
        "temp":round(random.uniform(24,28), 2),  
        "humidity":round(random.uniform(79,100), 2)
    }


@app.get("/api/sensor/recent")
async def get_reading_recent(limit: int = Query(20, ge=1, le=1000)):
    """Get recent sensor readings with optional limit"""
    
    # conn = get_db_connection()
    # cursor = conn.cursor()
    
    # cursor.execute("""
    #     SELECT datetime, wattage
    #     FROM readings
    #     ORDER BY datetime DESC
    #     LIMIT ?
    # """, (limit,))
    
    # rows = cursor.fetchall()
    # conn.close()
    
    ret_arr = []
    for i in range(0, limit):
        
        record = {
            "timestamp":f"{dt.datetime}",
            "voltage": round(random.uniform(0,12), 2),
            "wattage": round(random.uniform(0,20), 2),
            "temp":round(random.uniform(24,28), 2),  
            "humidity":round(random.uniform(0,100), 2)
        }
        ret_arr.append(record)
    
    
    return ret_arr


@app.get("/api/sensor/offsets")
async def get_sensor_offsets():
    """Get sensor calibration offsets from config"""
    try:
        data = json_op('r', 'sensor_offset.json5')
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read offsets: {str(e)}")


@app.post("/api/sensor/offsets")
async def update_sensor_offsets(offsets: Dict):
    """Update sensor calibration offsets"""
    try:
        data = json_op('r', 'sensor_offset.json5')
        if data:
            print(offsets)
            data = offsets
            json_op('w', 'sensor_offset.json5', data)
        return 200
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update offsets: {str(e)}")


@app.get("/api/sensor/readings/export", response_model=List[SensorReading])
async def export_readings():
    """Export all sensor readings from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT datetime, voltage, current, wattage, temp, humidity
        FROM readings
        ORDER BY datetime ASC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        SensorReading(
            voltage=row["voltage"],
            wattage=row["wattage"],
            ampere=row["current"],
            temperature=row["temp"],
            humidity=row["humidity"],
            timestamp=row["datetime"]
        )
        for row in rows
    ]


# ==================== PANEL CONTROL ENDPOINTS ====================


@app.get("/api/panel/angle")
async def get_panel_angle():
    """Get current panel position from control data"""
    try:
        data = json_op('r', 'control.json5')
        return data["realtime"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get position: {str(e)}")

@app.get("/api/panel/expected")
async def get_panel_expected_a():
    """Get current panel position from control data"""
    try:
        data = json_op('r', 'control.json5')
        return data["expected"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get position: {str(e)}")

@app.post("/api/panel/angle")
async def update_panel_angle(batch: dict):
    """Update panel position (manual control)"""
    try:
        data = json_op('r', 'control.json5')
        data["expected"] = { "yaw": batch["yaw"], "roll": batch["roll"]}
        json_op('w', 'control.json5', data)
        return 200
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update position: {str(e)}")


@app.get("/api/panel/curves")
async def get_curves() :
    """Get angle curves for time-based tracking"""
    try:
        data = json_op('r', 'control.json5')
        return data["curves"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get curves: {str(e)}")


@app.post("/api/panel/curves")
async def update_curves(batch: dict):
    """Update angle curves"""
    try:
        data = json_op('r', 'control.json5')

        if batch["type"] == "yaw":
            data["curves"]["yaw"] = batch["values"]
        elif batch["type"] == "roll":
            data["curves"]["roll"] = batch["values"]
        else:
            raise HTTPException(status_code=400, detail="Invalid curve type")

        print(data["curves"])
        json_op('w', 'control.json5', data)
        return 200
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update curves: {str(e)}")


@app.get("/api/panel/offset")
async def get_panel_offset():
    """Get current panel position from control data"""
    try:
        data = json_op('r', 'control.json5')
        return data["offset"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get position: {str(e)}")


@app.post("/api/panel/offset")
async def update_panel_offset(batch: dict):
    """Update panel position (manual control)"""
    try:
        data = json_op('r', 'control.json5')
        data["offset"] = {
            "yaw": batch["yaw"],
            "roll": batch["roll"]
        }
        data["range"] = {
            "yaw": [ 0 + batch["yaw"], 180 + batch["yaw"] ],
            "roll": [ 35 + batch["roll"], 135 + batch["roll"] ]
        }
        data["expected"] = { 
            "yaw": data["realtime"]["yaw"] + batch["yaw"], 
            "roll": data["realtime"]["roll"] + batch["roll"] 
        }
        for i in data["curves"]["yaw"]: i["yaw"] += data["offset"]["yaw"]
        print(data["curves":])
        for i in data["curves"]["roll"]: i += data["offset"]["roll"] 
        json_op('w', 'control.json5', data)
        return 200
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update position: {str(e)}")


@app.get("/api/panel/optimal")
async def get_optimal_angles():
    """Get recommended angles from solar calculation"""
    try:
        tz = pytz.timezone(TIMEZONE)
        current_time = dt.datetime.now(tz)
        
        # Generate optimal angles for the configured time range
        results = generate_optimal_angles(current_time, settings.op_start, settings.op_span_hours)
        
        # Extract yaw and roll arrays
        yaw_angles = [int(r["yaw"]) for r in results]
        roll_angles = [int(r["roll"]) for r in results]
        
        return {
            "yaw": yaw_angles,
            "roll":roll_angles
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate angles: {str(e)}")

@app.get("/api/panel/range")
async def get_panel_range():
    try:
        data = json_op('r', 'control.json5')
        return data["range"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get position: {str(e)}")


# ==================== SYSTEM ENDPOINTS ====================

@app.get("/api/system/tracking")
async def get_tracking_status():
    """Get panel tracking background task status"""
    return {
        "enabled": tracking_enabled,
        "running": tracking_task is not None and not tracking_task.done()
    }


@app.post("/api/system/tracking")
async def toggle_tracking(enable: bool):
    """Enable or disable panel tracking"""
    global tracking_enabled, tracking_task
    
    if enable and not tracking_enabled:
        tracking_enabled = True
        if tracking_task is None or tracking_task.done():
            tracking_task = asyncio.create_task(panel_tracking_loop())
        return {"message": "Tracking enabled"}
    elif not enable and tracking_enabled:
        tracking_enabled = False
        return {"message": "Tracking disabled"}
    
    return {"message": "No change"}


@app.get("/api/system/status", response_model=SystemStatus)
async def get_system_status():
    """Get system status and uptime"""
    import time
    import os
    
    try:
        # Try to read uptime from system
        if os.name == 'posix':
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = int(float(f.readline().split()[0]))
        else:
            uptime_seconds = 0
        
        return SystemStatus(
            status="running",
            uptime_seconds=uptime_seconds,
            firmware_version="1.0.0"
        )
    except Exception as e:
        return SystemStatus(
            status="unknown",
            uptime_seconds=0,
            firmware_version="1.0.0"
        )


@app.post("/api/system/status")
async def update_system_status(status_update: StatusUpdate):
    """Update system status"""
    # This could trigger system actions like restart, shutdown, etc.
    return {"message": f"System status updated to: {status_update.status}"}


# ==================== CONFIG ENDPOINTS ====================

@app.get("/api/config/api-server")
async def get_api_server():
    """Get API server URL configuration"""
    try:
        data = json_op('r', 'settings.json5')
        api_server = data.get("api_server", "http://localhost:8000")
        return {"value": api_server}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@app.post("/api/config/api-server")
async def update_api_server(config: ApiServerConfig):
    """Update API server URL"""
    try:
        data = json_op('r', 'settings.json5')
        if data:
            data["api_server"] = config.value
            json_op('w', 'settings.json5', data)
        return {"message": "API server config updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


@app.get("/api/config/angular-offset", response_model=AngularOffset)
async def get_angular_offset():
    """Get angular offsets for panel calibration"""
    try:
        data = json_op('r', 'control.json5')
        offsets = data.get("offsets", {"yaw": 0, "roll": 0})
        return AngularOffset(yaw=offsets.get("yaw", 0), roll=offsets.get("roll", 0))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get angular offset: {str(e)}")


@app.post("/api/config/angular-offset")
async def update_angular_offset(offset: AngularOffset):
    """Update angular offsets"""
    try:
        data = json_op('r', 'control.json5')
        if data:
            data["offsets"] = {"yaw": offset.yaw, "roll": offset.roll}
            json_op('w', 'control.json5', data)
        return {"message": "Angular offset updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update angular offset: {str(e)}")




# ==================== ROOT ENDPOINT ====================

@app.get("/")
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
            "external": "/api/external/*"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
