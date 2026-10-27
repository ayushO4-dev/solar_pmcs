"""Runtime configuration, read from environment variables or a .env file."""

import datetime as dt
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    database_url: str = "postgresql://spmc:spmc@localhost:5432/spmc"
    cors_origins: list[str] = ["*"]
    # Built frontend served at / when present (npm run build in frontend/)
    frontend_dist: str = "../frontend/dist"

    # Site location used for solar position calculation
    latitude: float = 19.9975
    longitude: float = 73.7898
    temperature_c: float = 32.0
    timezone: str = "Asia/Kolkata"

    # Operating window: first slot and how many hours of half-hour slots follow it
    op_start: dt.time = dt.time(6, 30)
    op_span_hours: int = 12
    elevation_lookup_timeout_s: float = 10.0

    # "simulated" generates fake readings; "hardware" reads the INA219 and DHT11
    sensor_mode: Literal["simulated", "hardware"] = "simulated"
    sample_interval_s: float = 5.0

    # Panel tracking: degrees moved per tick and seconds between ticks
    tracking_step_deg: float = 1.0
    tracking_interval_s: float = 0.5


settings = Settings()
