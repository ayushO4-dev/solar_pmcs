"""
Power and environment sensors.

    - INA219 (I2C): bus voltage, current and power
    - DHT11 (GPIO4): temperature and humidity

Every reader returns a dict with keys voltage (V), current (A), wattage (W),
temperature (°C) and humidity (%). A value is None when its sensor fails.
"""

import random
import time

READING_KEYS = ("voltage", "current", "wattage", "temperature", "humidity")


class INA219Sensor:
    def __init__(self, shunt_ohms=0.1, max_expected_amps=1.01, busnum=1):
        from ina219 import INA219

        self.ina = INA219(shunt_ohms, busnum=busnum, max_expected_amps=max_expected_amps)
        self.ina.configure(
            voltage_range=self.ina.RANGE_32V,
            gain=self.ina.GAIN_AUTO,
            bus_adc=self.ina.ADC_128SAMP,
            shunt_adc=self.ina.ADC_128SAMP)

    def read(self) -> dict | None:
        from ina219 import DeviceRangeError

        try:
            return {
                "voltage": self.ina.voltage(),
                "current": self.ina.current() / 1000,  # mA -> A
                "wattage": self.ina.power() / 1000,  # mW -> W
            }
        except DeviceRangeError as e:
            print(e)
            return None


class DHT11Sensor:
    PIN = 4  # BCM numbering (GPIO4)

    def __init__(self):
        import adafruit_dht
        import board

        self.sensor = adafruit_dht.DHT11(getattr(board, f"D{self.PIN}"))

    def read(self) -> dict | None:
        try:
            return {
                "temperature": round(self.sensor.temperature, 2),
                "humidity": round(self.sensor.humidity, 2),
            }
        except RuntimeError as error:
            # DHT11 reads fail often; the next sample will retry
            print(error.args[0])
            time.sleep(1)
            return None
        except Exception:
            self.sensor.exit()
            raise


class HardwareSensors:
    def __init__(self):
        self.ina = INA219Sensor()
        self.dht = DHT11Sensor()

    def read(self) -> dict:
        reading = dict.fromkeys(READING_KEYS)
        reading.update(self.ina.read() or {})
        reading.update(self.dht.read() or {})
        return reading


class SimulatedSensors:
    """Plausible random readings for development without the Pi hardware."""

    def read(self) -> dict:
        voltage = random.uniform(10, 12)
        wattage = random.uniform(15, 20)
        return {
            "voltage": round(voltage, 2),
            "current": round(wattage / voltage, 2),
            "wattage": round(wattage, 2),
            "temperature": round(random.uniform(24, 28), 2),
            "humidity": round(random.uniform(79, 100), 2),
        }


def make_sensor_reader(mode: str):
    return HardwareSensors() if mode == "hardware" else SimulatedSensors()
