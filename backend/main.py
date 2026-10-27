import datetime as dt
import json
import urllib.error
import urllib.parse
import urllib.request
import pytz
import pathlib
import sqlite3


# Input variables
LAT = 19.9975
LON = 73.7898
TEMPERATURE_C = 32.0
TIMEZONE = "Asia/Kolkata"
OP_HOURS = (630,12)
ELEVATION_LOOKUP_TIMEOUT_S = 10

    
def json_op(mode: str, filename: str, data=None):
    import json5
    with open(f"data/{filename}", mode) as f:
        if data: 
            json5.dump(data, f, indent=4)
        else: data = json5.load(f);
    return data


# def get_sensor_data() -> list:
    
#     import time

#     class INA219Sensor:
#         def __init__(self, shunt_ohms=0.1, max_expected_amps=1.01, busnum=1):
#             from ina219 import INA219
#             self.INA219 = INA219
#             self.shunt_ohms = shunt_ohms
#             self.max_expected_amps = max_expected_amps
#             self.busnum = busnum
#             self.ina = self.INA219(self.shunt_ohms, busnum=self.busnum, max_expected_amps=self.max_expected_amps)
#             self.ina.configure(
#                 voltage_range=self.ina.RANGE_32V,
#                 gain=self.ina.GAIN_AUTO,
#                 bus_adc=self.ina.ADC_128SAMP,
#                 shunt_adc=self.ina.ADC_128SAMP)

#         def read(self):
#             from ina219 import DeviceRangeError
#             try:
#                 voltage = self.ina.voltage()
#                 current = self.ina.current()
#                 power = self.ina.power() / 1000
                
#                 # print(f"\nBus Voltage: {voltage:.2f} V")
#                 # print(f"Bus Current: {current:.2f} mA")
#                 # print(f"Power: {power:.2f} W\n")
#                 # print("Supply Voltage: %.3f V" % self.ina.supply_voltage())
#                 # print("Shunt voltage: %.3f mV" % self.ina.shunt_voltage())
                
#                 return {"voltage": voltage, "current": current, "power": power}
#             except DeviceRangeError as e:
#                 print(e)
#                 return None
            
#     class DHT11Sensor:
#         def __init__(self):
#             import adafruit_dht
            
#             PIN = 4  # BCM numbering (GPIO4)
#             self.sensor = adafruit_dht.DHT11(PIN)
        
#         def read(self):
#             try:
#                 temperature = self.sensor.temperature
#                 humidity = self.sensor.humidity
#                 return {"temp": round(temperature, 2), "humidity": round(humidity, 2)}
#             except RuntimeError as error:
#                 print(error.args[0])
#                 time.sleep(1)
#             except Exception as error:
#                 self.sensor.exit()
#                 raise error

#     ina = INA219Sensor()
#     dht = DHT11Sensor()
#     return [ ina.read(), dht.read() ]


def get_ldr_readings() -> dict:
    """
    Read 4 LDR sensors using RC timing method (no ADC required).
    LDR placement: top-left, top-right, bottom-left, bottom-right
    
    Returns:
        dict: Dictionary with LDR readings and computed tracking deltas
            - "tl": top-left charge time (microseconds, lower = more light)
            - "tr": top-right charge time (microseconds)
            - "bl": bottom-left charge time (microseconds)
            - "br": bottom-right charge time (microseconds)
            - "yaw_delta": horizontal tracking error (left-right difference)
            - "roll_delta": vertical tracking error (top-bottom difference)
    
    Circuit for each LDR:
        GPIO pin ----+---- LDR ---- GND
                     |
                     +---- 1µF capacitor ---- GND
    
    Notes:
        - No external ADC needed
        - Lower charge time = more light (brighter)
        - Adjust capacitor value (0.1µF - 10µF) based on LDR sensitivity
        - For Raspberry Pi 5, uses RPi.GPIO or lgpio library
        - GPIO pins: 17 (TL), 27 (TR), 22 (BL), 23 (BR)
    """
    import RPi.GPIO as GPIO
    import time
    
    # GPIO pin assignments
    PIN_TL = 17  # Top-left
    PIN_TR = 27  # Top-right
    PIN_BL = 22  # Bottom-left
    PIN_BR = 23  # Bottom-right
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    def read_ldr_timing(pin: int, timeout: float = 0.1) -> float:
        """
        Measure RC charge time for a single LDR.
        Returns time in microseconds (lower = brighter light).
        """
        # Discharge capacitor
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.1)
        
        # Start timing capacitor charge
        GPIO.setup(pin, GPIO.IN)
        start = time.time()
        
        # Wait for pin to go HIGH (capacitor charged)
        while GPIO.input(pin) == GPIO.LOW:
            if time.time() - start > timeout:
                return timeout * 1_000_000  # Return max if timeout
        
        charge_time = (time.time() - start) * 1_000_000  # Convert to microseconds
        return charge_time
    
    # Read all 4 LDRs
    tl_value = read_ldr_timing(PIN_TL)
    tr_value = read_ldr_timing(PIN_TR)
    bl_value = read_ldr_timing(PIN_BL)
    br_value = read_ldr_timing(PIN_BR)
    
    # Calculate tracking deltas
    # Since lower time = more light, we invert the logic
    # Positive yaw_delta means more light on LEFT, need to move LEFT
    # Positive roll_delta means more light on TOP, need to tilt UP
    left_avg = (tl_value + bl_value) / 2
    right_avg = (tr_value + br_value) / 2
    top_avg = (tl_value + tr_value) / 2
    bottom_avg = (bl_value + br_value) / 2
    
    yaw_delta = left_avg - right_avg  # Inverted because lower=brighter
    roll_delta = bottom_avg - top_avg  # Inverted
    
    return {
        "tl": round(tl_value, 2),
        "tr": round(tr_value, 2),
        "bl": round(bl_value, 2),
        "br": round(br_value, 2),
        "yaw_delta": round(yaw_delta, 2),
        "roll_delta": round(roll_delta, 2)
    }


def save_data(sensor_data: list) -> None:
    """
    Save sensor readings to SQLite database.
    
    Args:
        sensor_data: List containing [INA219_dict, DHT11_dict]
                     INA219_dict = {"voltage": float, "current": float, "power": float}
                     DHT11_dict = {"temp": float, "humidity": float}
    
    Database:
        - File: data/sensor_readings.db
        - Table: readings
        - Columns: datetime, voltage, current, wattage, temp, humidity
    """
    
    # Create data directory if it doesn't exist
    pathlib.Path("data").mkdir(exist_ok=True)
    
    # Connect to SQLite database
    conn = sqlite3.connect("data/sensors.db")
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            datetime TEXT PRIMARY KEY,
            voltage REAL,
            current REAL,
            wattage REAL,
            temp REAL,
            humidity REAL
        )
    """)
    
    # Extract data from sensor readings
    ina_data = sensor_data[0] if sensor_data[0] else {}
    dht_data = sensor_data[1] if sensor_data[1] else {}
    
    # Get current timestamp
    tz = pytz.timezone(TIMEZONE)
    timestamp = dt.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    
    # Insert data
    cursor.execute("""
        INSERT OR REPLACE INTO readings (datetime, voltage, current, wattage, temp, humidity)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        ina_data.get("voltage"),
        ina_data.get("current"),
        ina_data.get("power"),  # Maps to wattage column
        dht_data.get("temp"),
        dht_data.get("humidity")
    ))
    
    conn.commit()
    conn.close()
    
        
def generate_optimal_angles(t: dt.datetime, _range: tuple) -> list:
    """
    Calculate optimal solar panel angular positioning data for a given time range.
    This function computes the sun's position (azimuth and altitude) and translates it
    into practical yaw and roll angles for solar panel orientation over a specified time span.
    Args:
        time (dt.datetime): The starting datetime for solar position calculations.
        _range (tuple): time range to calculate values within.         
    Returns:
        dict: A dictionary containing the last calculated solar positioning data with keys:
            - "time" (str): Time in "HH:MM" format
            - "_yaw" (float): Raw azimuth angle in degrees (0-360)
            - "_roll" (float): Raw tilt angle in degrees
            - "yaw" (int): Adjusted azimuth angle (0-180 degrees)
            - "roll" (int): Adjusted tilt angle accounting for panel inversion
            - "invert" (bool): Panel inversion flag (azimuth > 180°)
    Notes:
        - Uses pysolar library for solar position calculations
        - Fetches site elevation from Open-Meteo API for accuracy
        - Iterates through SPAN_HOURS starting from START_HOUR
        - Uses global constants: LAT, LON, START_HOUR, SPAN_HOURS, TEMPERATURE_C
        - Tilt is clamped to non-negative values when sun is beyond zenith
        - For azimuth > 180°, the angle is normalized and panel inversion is flagged
    """
    
    
    from pysolar.solar import get_altitude, get_azimuth

    def fetch_site_elevation(lat: float, lon: float) -> float:
        """Approximate elevation above mean sea level in meters using Open-Meteo."""
        
        params = urllib.parse.urlencode({"latitude": lat, "longitude": lon})
        url = f"https://api.open-meteo.com/v1/elevation?{params}"
        
        try:
            with urllib.request.urlopen(url, timeout=ELEVATION_LOOKUP_TIMEOUT_S) as response:
                payload = json.load(response)
        except (urllib.error.URLError, TimeoutError, ValueError):
            return 0.0

        elevation = payload.get("elevation")
        if isinstance(elevation, (int, float)):
            return float(elevation)
        if isinstance(elevation, list) and elevation:
            value = elevation[0]
            if isinstance(value, (int, float)):
                return float(value)
        return 0.0
    
    site_elevation = fetch_site_elevation(LAT, LON)
    
    results = list()

    for half_hour_offset in range((_range[1] * 2)-1):
        
        t = t.replace(hour=_range[0]//100, minute=_range[0]%100) + dt.timedelta(minutes=half_hour_offset * 30)
        elevation = get_altitude(LAT, LON, t, site_elevation, TEMPERATURE_C)
        _azimuth = get_azimuth(LAT, LON, t)
        _tilt = max(0.0, 90.0 - elevation)  # Prevent negative values when the sun is beyond zenith.

        azimuth = _azimuth
        tilt = _tilt
        invert = False
        if azimuth > 180.0:
            azimuth -= 180.0
            tilt = 180.0 - tilt
            invert = True

        record = {
            "time": t.strftime("%H:%M"),
            "_yaw": round(_azimuth, 2),
            "_roll": round(_tilt, 2),
            "yaw": round(azimuth),
            "roll": round(tilt),
            "invert": invert,
        }
        results.append(record)

    return results


def main() -> None:
    
    tz = pytz.timezone(TIMEZONE)
    time = dt.datetime.now(tz)

    results = generate_optimal_angles(time, OP_HOURS)
    
    
    
    
    data = json_op('r','control.json5')
    if data: data["optimal"] = results
    json_op('w', 'control.json5', data)


if __name__ == "__main__":
    main()