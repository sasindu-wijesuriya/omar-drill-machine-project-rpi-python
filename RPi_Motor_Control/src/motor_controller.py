"""
Motor Controller Module
Handles stepper motors, buttons, limit switches, and joystick input
Uses microsecond-precision timing for accurate stepper control
"""

import time
import threading
import logging
from typing import Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class PinState(Enum):
    """Pin state enumeration"""
    LOW = 0
    HIGH = 1


class StepperMotor:
    """
    Stepper motor controller with microsecond-precision pulse generation
    Mimics Arduino's delayMicroseconds() behavior for STEP/DIR control
    """
    
    def __init__(self, hw_interface, step_pin: int, dir_pin: int, name: str = "Motor"):
        """
        Initialize stepper motor
        
        Args:
            hw_interface: Hardware interface instance
            step_pin: GPIO pin for STEP signal
            dir_pin: GPIO pin for DIR signal
            name: Motor name for logging
        """
        self.hw = hw_interface
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.name = name
        
        # Setup pins
        self.hw.set_mode_output(self.step_pin, 0)
        self.hw.set_mode_output(self.dir_pin, 0)
        
        # State tracking
        self.current_direction = False
        self.pulse_state = False
        self.last_pulse_time = 0
        
        logger.info(f"StepperMotor '{name}' initialized: STEP={step_pin}, DIR={dir_pin}")
    
    def set_direction(self, direction: bool):
        """
        Set motor direction
        
        Args:
            direction: True for one direction, False for opposite
        """
        self.current_direction = direction
        self.hw.write(self.dir_pin, 1 if direction else 0)
    
    def step_pulse(self, high: bool):
        """
        Generate single step pulse (HIGH or LOW)
        
        Args:
            high: True for HIGH pulse, False for LOW
        """
        self.hw.write(self.step_pin, 1 if high else 0)
        self.pulse_state = high
    
    def step_blocking(self, steps: int, speed_us: int, direction: Optional[bool] = None,
                     check_callback: Optional[Callable[[], bool]] = None):
        """
        Execute blocking steps with precise timing
        
        Args:
            steps: Number of steps to execute
            speed_us: Microseconds between pulses
            direction: Direction override (None = keep current)
            check_callback: Optional callback to check for stop conditions (return True to stop)
        
        Returns:
            Number of steps actually executed (may be less if interrupted)
        """
        if direction is not None:
            self.set_direction(direction)
        
        executed_steps = 0
        
        for i in range(steps):
            # Check for interruption
            if check_callback and check_callback():
                logger.debug(f"{self.name}: Interrupted at step {i}/{steps}")
                break
            
            # HIGH pulse
            self.step_pulse(True)
            self._delay_microseconds(speed_us)
            
            # LOW pulse
            self.step_pulse(False)
            self._delay_microseconds(speed_us)
            
            executed_steps += 1
        
        return executed_steps
    
    def _delay_microseconds(self, microseconds: int):
        """
        Delay in microseconds (mimics Arduino delayMicroseconds)
        
        Args:
            microseconds: Delay duration in microseconds
        """
        time.sleep(microseconds / 1_000_000.0)
    
    def stop(self):
        """Stop motor immediately"""
        self.hw.write(self.step_pin, 0)
        self.hw.write(self.dir_pin, 0)
        logger.debug(f"{self.name}: Stopped")


class NonBlockingStepper:
    """
    Non-blocking stepper motor controller for concurrent operation
    Used in automatic cycles where multiple motors need to run simultaneously
    """
    
    def __init__(self, hw_interface, step_pin: int, dir_pin: int, name: str = "Motor"):
        self.hw = hw_interface
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.name = name
        
        # Setup pins
        self.hw.set_mode_output(self.step_pin, 0)
        self.hw.set_mode_output(self.dir_pin, 0)
        
        # State
        self.enabled = False
        self.speed_us = 2000
        self.direction = False
        self.pulse_state = False
        self.last_pulse_micros = 0
        
        logger.info(f"NonBlockingStepper '{name}' initialized")
    
    def set_speed(self, speed_us: int):
        """Set pulse interval in microseconds"""
        self.speed_us = speed_us
    
    def set_direction(self, direction: bool):
        """Set direction"""
        self.direction = direction
        self.hw.write(self.dir_pin, 1 if direction else 0)
    
    def enable(self):
        """Enable motor movement"""
        self.enabled = True
        self.last_pulse_micros = self.hw.get_current_tick()
    
    def disable(self):
        """Disable motor movement"""
        self.enabled = False
        self.hw.write(self.step_pin, 0)
    
    def update(self) -> bool:
        """
        Update motor state (call frequently in main loop)
        
        Returns:
            True if a step was executed, False otherwise
        """
        if not self.enabled:
            return False
        
        current_micros = self.hw.get_current_tick()
        elapsed = self._tick_diff(current_micros, self.last_pulse_micros)
        
        if elapsed >= self.speed_us:
            self.last_pulse_micros = current_micros
            self.pulse_state = not self.pulse_state
            self.hw.write(self.step_pin, 1 if self.pulse_state else 0)
            return True
        
        return False
    
    def _tick_diff(self, current: int, previous: int) -> int:
        """Calculate tick difference handling overflow"""
        if current >= previous:
            return current - previous
        else:
            # Handle 32-bit overflow
            return (0xFFFFFFFF - previous) + current
    
    def stop(self):
        """Stop motor"""
        self.disable()


class Button:
    """
    Button input handler with edge detection
    Detects rising edge (button press) with debouncing
    """
    
    def __init__(self, hw_interface, pin: int, name: str = "Button", pull_up: bool = True):
        """
        Initialize button
        
        Args:
            hw_interface: Hardware interface instance
            pin: GPIO pin number
            name: Button name for logging
            pull_up: Use pull-up resistor
        """
        self.hw = hw_interface
        self.pin = pin
        self.name = name
        
        # Setup pin
        self.hw.set_mode_input(self.pin, pull_up=pull_up)
        
        # State tracking
        self.last_state = self.hw.read(self.pin)
        self.last_check_time = time.time()
        self.debounce_time = 0.05  # 50ms debounce
        
        logger.info(f"Button '{name}' initialized on pin {pin}")
    
    def is_pressed(self) -> bool:
        """Check if button is currently pressed (active LOW with pull-up)"""
        return self.hw.read(self.pin) == 0
    
    def check_rising_edge(self) -> bool:
        """
        Check for rising edge (button press transition)
        Arduino pattern: if (btnPasado != digitalRead(btn)) { btnPasado = digitalRead(btn); if (btnPasado) {...} }
        
        Returns:
            True if button was just pressed, False otherwise
        """
        current_time = time.time()
        
        # Debounce check
        if (current_time - self.last_check_time) < self.debounce_time:
            return False
        
        current_state = self.hw.read(self.pin)
        
        # Detect rising edge (0 -> 1 transition for active-low button)
        if current_state != self.last_state:
            self.last_state = current_state
            self.last_check_time = current_time
            
            # Rising edge detected (button pressed)
            if current_state == 1:
                logger.debug(f"Button '{self.name}' pressed")
                return True
        
        return False


class LimitSwitch:
    """
    Limit switch input handler with edge detection
    """
    
    def __init__(self, hw_interface, pin: int, name: str = "Limit", pull_up: bool = True):
        """
        Initialize limit switch
        
        Args:
            hw_interface: Hardware interface instance
            pin: GPIO pin number
            name: Switch name for logging
            pull_up: Use pull-up resistor
        """
        self.hw = hw_interface
        self.pin = pin
        self.name = name
        
        # Setup pin
        self.hw.set_mode_input(self.pin, pull_up=pull_up)
        
        # State tracking
        self.last_state = self.hw.read(self.pin)
        
        logger.info(f"LimitSwitch '{name}' initialized on pin {pin}")
    
    def is_triggered(self) -> bool:
        """Check if limit switch is triggered"""
        return self.hw.read(self.pin) == 1
    
    def check_rising_edge(self) -> bool:
        """
        Check for rising edge (switch triggered)
        
        Returns:
            True if switch was just triggered, False otherwise
        """
        current_state = self.hw.read(self.pin)
        
        if current_state != self.last_state:
            self.last_state = current_state
            
            # Rising edge detected
            if current_state == 1:
                logger.debug(f"LimitSwitch '{self.name}' triggered")
                return True
        
        return False
    
    def wait_for_trigger(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for limit switch to be triggered
        
        Args:
            timeout: Maximum wait time in seconds (None = wait forever)
        
        Returns:
            True if triggered, False if timeout
        """
        start_time = time.time()
        
        while True:
            if self.check_rising_edge():
                return True
            
            if timeout and (time.time() - start_time) > timeout:
                logger.warning(f"LimitSwitch '{self.name}' wait timeout")
                return False
            
            time.sleep(0.001)  # 1ms poll interval


class Joystick:
    """
    Analog joystick handler (via ADC)
    Maps Arduino analogRead() behavior
    """
    
    def __init__(self, adc_channel: int = 0, center_min: int = 352, center_max: int = 652,
                 adc_min: int = 0, adc_max: int = 1023, simulate: bool = False):
        """
        Initialize joystick
        
        Args:
            adc_channel: ADC channel number
            center_min: Center deadzone minimum value
            center_max: Center deadzone maximum value
            adc_min: ADC minimum value
            adc_max: ADC maximum value
            simulate: Use simulated ADC values
        """
        self.adc_channel = adc_channel
        self.center_min = center_min
        self.center_max = center_max
        self.adc_min = adc_min
        self.adc_max = adc_max
        self.simulate = simulate
        
        # Simulated position
        self.simulated_value = (center_min + center_max) // 2
        
        if not simulate:
            try:
                # Try to import MCP3008 library (for real hardware)
                from gpiozero import MCP3008
                self.adc = MCP3008(channel=adc_channel)
                logger.info(f"Joystick initialized on ADC channel {adc_channel}")
            except ImportError:
                logger.warning("gpiozero not available, using simulated joystick")
                self.simulate = True
        else:
            logger.info(f"Joystick initialized (SIMULATED)")
    
    def read_raw(self) -> int:
        """
        Read raw ADC value (0-1023, Arduino analogRead equivalent)
        
        Returns:
            ADC value (0-1023)
        """
        if self.simulate:
            return self.simulated_value
        else:
            # Convert 0-1 voltage to 0-1023 ADC range
            voltage = self.adc.value
            return int(voltage * self.adc_max)
    
    def get_direction(self) -> int:
        """
        Get joystick direction
        
        Returns:
            -1 for backward, 0 for center, 1 for forward
        """
        value = self.read_raw()
        
        if value < self.center_min:
            return -1  # Backward/Home direction
        elif value > self.center_max:
            return 1   # Forward/Final direction
        else:
            return 0   # Center/Neutral
    
    def get_speed_mapped(self, min_speed: int, max_speed: int) -> int:
        """
        Get mapped speed value based on joystick position
        
        Args:
            min_speed: Minimum speed value (fastest)
            max_speed: Maximum speed value (slowest)
        
        Returns:
            Mapped speed value
        """
        value = self.read_raw()
        direction = self.get_direction()
        
        if direction == 0:
            return max_speed  # Center = slowest/stopped
        elif direction == -1:
            # Map from center_min to 0 -> max_speed to min_speed
            return self._map_value(value, 0, self.center_min, min_speed, max_speed)
        else:  # direction == 1
            # Map from center_max to adc_max -> max_speed to min_speed
            return self._map_value(value, self.center_max, self.adc_max, max_speed, min_speed)
    
    def _map_value(self, value: int, in_min: int, in_max: int, out_min: int, out_max: int) -> int:
        """Arduino map() function equivalent"""
        return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)
    
    def set_simulated_value(self, value: int):
        """Set simulated joystick value for testing"""
        self.simulated_value = max(self.adc_min, min(self.adc_max, value))
        logger.debug(f"Joystick simulated value set to {self.simulated_value}")
