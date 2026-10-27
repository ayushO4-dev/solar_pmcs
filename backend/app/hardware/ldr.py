"""
LDR light sensors for sun tracking.

The 4 LDRs are wired to an Arduino, which samples them and streams "a,b,c,d"
lines to the Pi over USB serial. None of the LDRs use Pi GPIO pins.
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
