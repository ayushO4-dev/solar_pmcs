"""Solar position calculation for optimal panel angles."""

import datetime as dt
import json
import urllib.error
import urllib.parse
import urllib.request

from pysolar.solar import get_altitude, get_azimuth

from .config import settings

_elevation_cache: dict[tuple[float, float], float] = {}


def fetch_site_elevation(lat: float, lon: float) -> float:
    """Approximate elevation above mean sea level in meters using Open-Meteo.

    Successful lookups are cached; failures return 0.0 and are retried next call.
    """
    if (lat, lon) in _elevation_cache:
        return _elevation_cache[(lat, lon)]

    params = urllib.parse.urlencode({"latitude": lat, "longitude": lon})
    url = f"https://api.open-meteo.com/v1/elevation?{params}"

    try:
        with urllib.request.urlopen(url, timeout=settings.elevation_lookup_timeout_s) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, ValueError):
        return 0.0

    elevation = payload.get("elevation")
    if isinstance(elevation, list) and elevation:
        elevation = elevation[0]
    if not isinstance(elevation, (int, float)):
        return 0.0

    _elevation_cache[(lat, lon)] = float(elevation)
    return float(elevation)


def generate_optimal_angles(day: dt.datetime, start: dt.time, span_hours: int) -> list[dict]:
    """
    Calculate optimal solar panel yaw/roll for half-hour slots across a day.

    Args:
        day: Timezone-aware datetime whose date is used for the calculation.
        start: Time of the first slot.
        span_hours: Number of hours covered; produces (span_hours * 2) - 1 slots.

    Returns:
        A list of records with keys:
            - "time" (str): Slot time in "HH:MM" format
            - "_yaw" (float): Raw azimuth angle in degrees (0-360)
            - "_roll" (float): Raw tilt angle in degrees
            - "yaw" (int): Adjusted azimuth angle (0-180 degrees)
            - "roll" (int): Adjusted tilt angle accounting for panel inversion
            - "invert" (bool): Panel inversion flag (azimuth > 180°)
    """
    site_elevation = fetch_site_elevation(settings.latitude, settings.longitude)
    first_slot = day.replace(hour=start.hour, minute=start.minute, second=0, microsecond=0)

    results = []
    for half_hour_offset in range((span_hours * 2) - 1):
        t = first_slot + dt.timedelta(minutes=half_hour_offset * 30)
        elevation = get_altitude(settings.latitude, settings.longitude, t,
                                 site_elevation, settings.temperature_c)
        _azimuth = get_azimuth(settings.latitude, settings.longitude, t)
        _tilt = max(0.0, 90.0 - elevation)  # Prevent negative values when the sun is beyond zenith.

        azimuth = _azimuth
        tilt = _tilt
        invert = False
        if azimuth > 180.0:
            azimuth -= 180.0
            tilt = 180.0 - tilt
            invert = True

        results.append({
            "time": t.strftime("%H:%M"),
            "_yaw": round(_azimuth, 2),
            "_roll": round(_tilt, 2),
            "yaw": round(azimuth),
            "roll": round(tilt),
            "invert": invert,
        })

    return results
