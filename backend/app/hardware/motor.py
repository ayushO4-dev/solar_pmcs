#!/usr/bin/env python3
"""
Monotonic stepper motor controller with drift correction.

Motor: JK42HS60-1684
Driver: TB6600
Raspberry Pi 5 - gpiod v2.x
Mode: full-step (200 steps/rev)
"""

import time
import gpiod
from gpiod.line import Direction, Value
import threading

class StepperMotor:
    """Stepper motor controller with monotonic timing and drift correction."""
    
    MIN_HALF_PERIOD = 0.0006  # Minimum safe half period (seconds)
    COARSE_SLEEP_THRESHOLD = 0.005  # Threshold for coarse sleep
    FINE_SLEEP_THRESHOLD = 0.0005  # Threshold for fine sleep
    
    def __init__(self, step_pin=17, dir_pin=27, enable_pin=22,
                 steps_per_rev=200, chip="/dev/gpiochip4"):
        """
        Initialize stepper motor controller.
        
        Args:
            step_pin: GPIO pin for step signal
            dir_pin: GPIO pin for direction signal
            enable_pin: GPIO pin for enable signal
            steps_per_rev: Number of steps per revolution
            chip: GPIO chip device path
        """
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.enable_pin = enable_pin
        self.steps_per_rev = steps_per_rev

        # Request GPIO lines as outputs
        self.request = gpiod.request_lines(
            chip,
            consumer="stepper_monotonic_drift_fix",
            config={
                step_pin: gpiod.LineSettings(
                    direction=Direction.OUTPUT,
                    output_value=Value.INACTIVE
                ),
                dir_pin: gpiod.LineSettings(
                    direction=Direction.OUTPUT,
                    output_value=Value.INACTIVE
                ),
                enable_pin: gpiod.LineSettings(
                    direction=Direction.OUTPUT,
                    output_value=Value.ACTIVE
                ),
            }
        )
        print(f"[INIT] Stepper ready ({self.steps_per_rev} steps/rev) on {chip}")

    def enable(self):
        """Enable the motor (LOW signal)."""
        self.request.set_value(self.enable_pin, Value.INACTIVE)
        print("[MOTOR] Enabled")

    def disable(self):
        """Disable the motor (HIGH signal)."""
        self.request.set_value(self.enable_pin, Value.ACTIVE)
        print("[MOTOR] Disabled")

    def set_direction(self, clockwise=True):
        """Set motor rotation direction."""
        direction_value = Value.ACTIVE if clockwise else Value.INACTIVE
        self.request.set_value(self.dir_pin, direction_value)

    def _send_pulse(self, half_period):
        """
        Send a single step pulse.
        
        Args:
            half_period: Duration of HIGH signal in seconds
        """
        self.request.set_value(self.step_pin, Value.ACTIVE)
        time.sleep(half_period)
        self.request.set_value(self.step_pin, Value.INACTIVE)

    def _wait_for_target_time(self, target_time):
        """
        Wait until target time using adaptive sleep strategy.
        
        Uses coarse sleep for long waits, fine sleep for medium waits,
        and busy-wait for precise timing.
        
        Args:
            target_time: Target monotonic time to wait for
        """
        while True:
            now = time.monotonic()
            time_remaining = target_time - now
            
            if time_remaining <= 0:
                break
            
            if time_remaining > self.COARSE_SLEEP_THRESHOLD:
                time.sleep(min(0.003, time_remaining))
            elif time_remaining > self.FINE_SLEEP_THRESHOLD:
                time.sleep(min(0.0003, time_remaining))
            # For sub-millisecond precision, busy-wait
    
    def move_steps(self, steps, half_period=0.0025, clockwise=True):
        """
        Move specified number of steps with drift correction.
        
        Uses monotonic timing to maintain precise step intervals and
        automatically resyncs if timing drifts too far.
        
        Args:
            steps: Number of steps to move
            half_period: Duration of HIGH pulse in seconds (full period = 2x)
            clockwise: Direction of rotation
        """
        # Enforce minimum safe timing
        half_period = max(half_period, self.MIN_HALF_PERIOD)
        total_period = half_period * 2.0
        
        self.set_direction(clockwise)
        print(f"[MOVE] {steps} steps, half_period={half_period:.6f}s, "
              f"period={total_period:.6f}s")

        # Initialize timing schedule
        base_time = time.monotonic()
        next_time = base_time + total_period

        print(int(steps))

        for i in range(int(steps)):
            now = time.monotonic()
            
            # Resync if we've fallen behind by more than one period
            if now > next_time + total_period:
                lag = now - next_time
                print(f"[WARN] Behind schedule by {lag:.6f}s on step {i}. "
                      f"Resyncing.")
                next_time = now + total_period

            # Wait until target start time for this pulse
            target_start = next_time - total_period
            self._wait_for_target_time(target_start)

            # Send the step pulse
            self._send_pulse(half_period)

            # Schedule next pulse
            next_time += total_period

        print(f"[DONE] Completed {steps} steps")

    def rotate_revolutions(self, revolutions=1, clockwise=True, half_period=0.0025):
        """
        Rotate motor for specified number of revolutions.
        
        Args:
            revolutions: Number of complete revolutions
            clockwise: Direction of rotation
            half_period: Duration of HIGH pulse in seconds
        """
        total_steps = self.steps_per_rev * revolutions
        self.move_steps(total_steps, half_period=half_period, clockwise=clockwise)

    def cleanup(self):
        """Clean up GPIO resources and disable motor."""
        self.disable()
        try:
            self.request.release()
        except Exception:
            pass
        print("[CLEANUP] GPIO released and motor disabled")


def main():
    """Test routine for stepper motor."""
    m1 = StepperMotor(
        step_pin=17,
        dir_pin=27,
        enable_pin=22,
        steps_per_rev=3200,
        chip="/dev/gpiochip4"
    )
    
    m2 = StepperMotor(
        step_pin=24,
        dir_pin=25,
        enable_pin=16,
        steps_per_rev=3200,
        chip="/dev/gpiochip4"
    ) 
    
    try:
        m1.enable()
        m2.enable()
        time.sleep(0.5)

        # Conservative timing: 25ms half period = 50ms full period (~10 RPM)
        half_period = 0.008
        print("\n-- Test: 1 revolution clockwise --")
        
        # Create threads for simultaneous motor movement
        thread1 = threading.Thread(target=m1.rotate_revolutions, 
                      args=(0.5, True, half_period))
        thread2 = threading.Thread(target=m2.rotate_revolutions, 
                      args=(0.3, True, half_period))

        thread3 = threading.Thread(target=m1.rotate_revolutions, 
                      args=(0.5, False, half_period))
        thread4 = threading.Thread(target=m2.rotate_revolutions, 
                      args=(0.3, False, half_period))

        
        while True:
        
        
            # Start both motors simultaneously
            thread1.start()
            thread2.start()
            
            # Wait for both motors to complete
            thread1.join()
            thread2.join()

            thread3.start()
            thread4.start()

            thread3.join()
            thread4.join()
        
        
    except KeyboardInterrupt:
        print("\n[INTERRUPT] User stopped.")
    finally:
        m1.cleanup()
        m2.cleanup()


if __name__ == "__main__":
    main()
