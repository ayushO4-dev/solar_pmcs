"""
LDR light sensors for sun tracking.

Two wiring options are supported:
    - ArduinoLdrReader: an Arduino samples 4 LDRs and streams "a,b,c,d" lines over serial.
    - read_rc_ldrs: LDRs wired directly to Pi GPIO, measured with the RC timing method.
"""

import time


class ArduinoLdrReader:
    """Reads comma-separated LDR values streamed by an Arduino over serial."""

    def __init__(self, port="/dev/ttyACM0", baudrate=9600):
        """
        Open the serial port (check with: ls /dev/ttyACM* or ls /dev/ttyUSB*).
        """
        import serial

        self.ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # Wait for Arduino to reset

    def read(self) -> list[int] | None:
        """Return the next 4 LDR values, or None if the line is empty or malformed."""
        line = self.ser.readline().decode("utf-8").strip()
        if not line:
            return None
        try:
            values = [int(x) for x in line.split(",")]
        except ValueError:
            print(f"Invalid data: {line}")
            return None
        return values if len(values) == 4 else None

    def close(self):
        self.ser.close()


def read_rc_ldrs() -> dict:
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

        return (time.time() - start) * 1_000_000  # Convert to microseconds

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


if __name__ == "__main__":
    reader = ArduinoLdrReader()
    print("Receiving LDR data from Arduino...\n")
    try:
        while True:
            ldr_values = reader.read()
            if ldr_values:
                print(f"LDR1: {ldr_values[0]}, LDR2: {ldr_values[1]}, "
                      f"LDR3: {ldr_values[2]}, LDR4: {ldr_values[3]}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopped by user.")
        reader.close()
