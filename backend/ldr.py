import serial
import time

# Open serial port (check with: ls /dev/ttyACM* or ls /dev/ttyUSB*)
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(2)  # Wait for Arduino to reset

print("Receiving LDR data from Arduino...\n")

try:
    while True:
        line = ser.readline().decode('utf-8').strip()
        print(line)
        if line:
            try:
                ldr_values = [int(x) for x in line.split(',')]
                print(f"LDR1: {ldr_values[0]}, LDR2: {ldr_values[1]}, LDR3: {ldr_values[2]}, LDR4: {ldr_values[3]}")
            except:
                print(f"Invalid data: {line}")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nStopped by user.")
    ser.close()
