"""
Hardware Interface Layer - GPIO Abstraction
Provides unified interface for real pigpio and simulated GPIO operations
"""

import sys
import time
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)


class HardwareInterface:
    """Abstract base for hardware operations"""
    
    def __init__(self, simulate: bool = False):
        self.simulate = simulate
        self.pi = None
        self._setup_gpio()
    
    def _setup_gpio(self):
        """Initialize GPIO interface based on simulation mode"""
        raise NotImplementedError
    
    def set_mode(self, pin: int, mode: int):
        raise NotImplementedError
    
    def set_pull_up_down(self, pin: int, pud: int):
        raise NotImplementedError
    
    def read(self, pin: int) -> int:
        raise NotImplementedError
    
    def write(self, pin: int, value: int):
        raise NotImplementedError
    
    def hardware_PWM(self, pin: int, frequency: int, dutycycle: int):
        raise NotImplementedError
    
    def set_mode_input(self, pin: int, pull_up: bool = False):
        raise NotImplementedError
    
    def set_mode_output(self, pin: int, initial_value: int = 0):
        raise NotImplementedError
    
    def cleanup(self):
        raise NotImplementedError


class RealHardwareInterface(HardwareInterface):
    """Real hardware using pigpio"""
    
    def _setup_gpio(self):
        try:
            import pigpio
            self.pi = pigpio.pi()
            
            if not self.pi.connected:
                raise RuntimeError("Could not connect to pigpiod daemon. Is it running?")
            
            logger.info("Connected to pigpiod successfully")
            
            # Store pigpio constants
            self.INPUT = pigpio.INPUT
            self.OUTPUT = pigpio.OUTPUT
            self.PUD_OFF = pigpio.PUD_OFF
            self.PUD_UP = pigpio.PUD_UP
            self.PUD_DOWN = pigpio.PUD_DOWN
            
        except ImportError:
            raise ImportError(
                "pigpio not installed. Install with: pip install pigpio\n"
                "Also ensure pigpiod daemon is running: sudo systemctl start pigpiod"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize pigpio: {e}")
    
    def set_mode(self, pin: int, mode: int):
        """Set pin mode (INPUT/OUTPUT)"""
        self.pi.set_mode(pin, mode)
    
    def set_pull_up_down(self, pin: int, pud: int):
        """Set pull up/down resistor"""
        self.pi.set_pull_up_down(pin, pud)
    
    def read(self, pin: int) -> int:
        """Read digital pin value"""
        return self.pi.read(pin)
    
    def write(self, pin: int, value: int):
        """Write digital pin value"""
        self.pi.write(pin, value)
    
    def hardware_PWM(self, pin: int, frequency: int, dutycycle: int):
        """Generate hardware PWM (for precise stepper timing)"""
        self.pi.hardware_PWM(pin, frequency, dutycycle)
    
    def set_mode_input(self, pin: int, pull_up: bool = False):
        """Configure pin as input with optional pull-up"""
        self.set_mode(pin, self.INPUT)
        if pull_up:
            self.set_pull_up_down(pin, self.PUD_UP)
        else:
            self.set_pull_up_down(pin, self.PUD_OFF)
    
    def set_mode_output(self, pin: int, initial_value: int = 0):
        """Configure pin as output with initial value"""
        self.set_mode(pin, self.OUTPUT)
        self.write(pin, initial_value)
    
    def get_current_tick(self) -> int:
        """Get current microsecond tick"""
        return self.pi.get_current_tick()
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        if self.pi:
            self.pi.stop()
            logger.info("pigpio connection closed")


class SimulatedHardwareInterface(HardwareInterface):
    """Simulated hardware for development/testing"""
    
    def _setup_gpio(self):
        logger.info("Initializing SIMULATED GPIO interface")
        
        # Simulate GPIO state
        self._pin_modes = {}
        self._pin_values = {}
        self._pin_pull = {}
        self._start_time = time.time()
        
        # Mock constants
        self.INPUT = 0
        self.OUTPUT = 1
        self.PUD_OFF = 0
        self.PUD_UP = 1
        self.PUD_DOWN = 2
        
        # Simulate limit switches (default not triggered)
        self._simulated_limits = {
            13: 0,  # finHome - not at home
            19: 0,  # finFinal - not at final
            6: 1,   # switchS - safety switch ON (active high)
        }
        
        # Simulate buttons (default not pressed)
        self._simulated_buttons = {
            17: 0,  # btnReset
            27: 0,  # btnStart
            22: 0,  # btnStop
            5: 0,   # btnTala
        }
        
        logger.info("Simulated GPIO initialized - Use this for development only!")
    
    def set_mode(self, pin: int, mode: int):
        """Set pin mode (INPUT/OUTPUT)"""
        self._pin_modes[pin] = mode
        logger.debug(f"[SIM] Pin {pin} set to {'INPUT' if mode == self.INPUT else 'OUTPUT'}")
    
    def set_pull_up_down(self, pin: int, pud: int):
        """Set pull up/down resistor"""
        self._pin_pull[pin] = pud
        logger.debug(f"[SIM] Pin {pin} pull resistor: {pud}")
    
    def read(self, pin: int) -> int:
        """Read digital pin value"""
        # Return simulated values for switches and buttons
        if pin in self._simulated_limits:
            return self._simulated_limits[pin]
        if pin in self._simulated_buttons:
            return self._simulated_buttons[pin]
        
        # Default to pull-up behavior
        return self._pin_values.get(pin, 1 if self._pin_pull.get(pin) == self.PUD_UP else 0)
    
    def write(self, pin: int, value: int):
        """Write digital pin value"""
        # Update the appropriate simulation dictionary so read() returns the correct value
        if pin in self._simulated_limits:
            self._simulated_limits[pin] = value
        elif pin in self._simulated_buttons:
            self._simulated_buttons[pin] = value
        else:
            self._pin_values[pin] = value
        # Don't log every pulse (too verbose), only state changes
        # logger.debug(f"[SIM] Pin {pin} = {value}")
    
    def hardware_PWM(self, pin: int, frequency: int, dutycycle: int):
        """Simulate hardware PWM"""
        logger.debug(f"[SIM] PWM on pin {pin}: freq={frequency}Hz, duty={dutycycle/10000}%")
    
    def set_mode_input(self, pin: int, pull_up: bool = False):
        """Configure pin as input with optional pull-up"""
        self.set_mode(pin, self.INPUT)
        if pull_up:
            self.set_pull_up_down(pin, self.PUD_UP)
        else:
            self.set_pull_up_down(pin, self.PUD_OFF)
    
    def set_mode_output(self, pin: int, initial_value: int = 0):
        """Configure pin as output with initial value"""
        self.set_mode(pin, self.OUTPUT)
        self.write(pin, initial_value)
    
    def get_current_tick(self) -> int:
        """Get current microsecond tick (simulated)"""
        return int((time.time() - self._start_time) * 1000000)
    
    def simulate_button_press(self, button_name: str):
        """Simulate button press for testing"""
        pin_map = {
            'reset': 17,
            'start': 27,
            'stop': 22,
            'tala': 5
        }
        if button_name in pin_map:
            pin = pin_map[button_name]
            self._simulated_buttons[pin] = 0
            logger.info(f"[SIM] Button '{button_name}' pressed (pin {pin})")
    
    def simulate_button_release(self, button_name: str):
        """Simulate button release for testing"""
        pin_map = {
            'reset': 17,
            'start': 27,
            'stop': 22,
            'tala': 5
        }
        time.sleep(0.1)  # Debounce delay
        if button_name in pin_map:
            pin = pin_map[button_name]
            self._simulated_buttons[pin] = 1
            logger.info(f"[SIM] Button '{button_name}' released (pin {pin})")
    
    def simulate_limit_switch(self, switch_name: str, triggered: bool):
        """Simulate limit switch state"""
        pin_map = {
            'home': 13,
            'final': 19,
            'safety': 6
        }
        if switch_name in pin_map:
            pin = pin_map[switch_name]
            self._simulated_limits[pin] = 1 if triggered else 0
            logger.info(f"[SIM] Limit switch '{switch_name}' {'TRIGGERED' if triggered else 'RELEASED'}")
    
    def cleanup(self):
        """Cleanup simulated GPIO"""
        logger.info("Simulated GPIO cleanup")


def get_hardware_interface(simulate: bool = False) -> HardwareInterface:
    """
    Factory function to get appropriate hardware interface
    
    Args:
        simulate: If True, use simulated GPIO. If False, try real hardware.
    
    Returns:
        HardwareInterface instance (Real or Simulated)
    """
    # Always try to use pigpio first (could be real or mock)
    try:
        logger.info("Attempting to use pigpio interface (real or mock)")
        return RealHardwareInterface(simulate=False)
    except (ImportError, RuntimeError) as e:
        if simulate:
            logger.warning(f"Could not initialize pigpio: {e}")
            logger.warning("Falling back to SIMULATED hardware interface")
            return SimulatedHardwareInterface(simulate=True)
        else:
            # If not simulating and can't get real hardware, raise error
            raise RuntimeError(f"Failed to initialize real hardware: {e}")


# For convenience
def create_gpio_interface(simulate: bool = False) -> HardwareInterface:
    """Alias for get_hardware_interface"""
    return get_hardware_interface(simulate)
