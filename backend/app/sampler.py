"""Background task that samples the sensors and stores readings in Postgres."""

import asyncio

from . import db
from .config import settings
from .hardware.sensors import READING_KEYS, make_sensor_reader


async def _sample(reader) -> None:
    # Hardware reads block (I2C, DHT11 bit-banging), so keep them off the event loop
    reading = await asyncio.to_thread(reader.read)
    offsets = {row["sensor"]: row["value"] for row in await db.fetch_all("SELECT sensor, value FROM sensor_offsets")}

    values = [
        None if reading.get(key) is None else round(reading[key] + offsets.get(key, 0), 3)
        for key in READING_KEYS
    ]
    await db.execute(
        f"INSERT INTO sensor_readings ({', '.join(READING_KEYS)}) VALUES (%s, %s, %s, %s, %s)",
        values,
    )


async def run() -> None:
    reader = make_sensor_reader(settings.sensor_mode)
    print(f"[Sampler] Reading {settings.sensor_mode} sensors every {settings.sample_interval_s}s")
    while True:
        try:
            await _sample(reader)
        except Exception as e:
            print(f"[Sampler Error] {e}")
        await asyncio.sleep(settings.sample_interval_s)
