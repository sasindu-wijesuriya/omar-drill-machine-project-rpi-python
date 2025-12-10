"""
GPIO Monitor and Control Module
Provides real-time GPIO pin state monitoring and control for testing
"""

import logging
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PinType(Enum):
    """GPIO Pin Type Classification"""
    OUTPUT = "OUTPUT"
    INPUT = "INPUT"
    UNUSED = "UNUSED"


class PinFunction(Enum):
    """GPIO Pin Function Classification"""
    MOTOR_STEP = "Motor STEP"
    MOTOR_DIR = "Motor DIR"
    BUTTON = "Button"
    LIMIT_SWITCH = "Limit Switch"
    SAFETY_SWITCH = "Safety Switch"
    ADC = "ADC"
    I2C = "I2C"
    UNUSED = "Unused"


@dataclass
class PinInfo:
    """GPIO Pin Information"""
    pin: int
    type: PinType
    function: PinFunction
    name: str
    description: str
    current_value: int = 0
    can_write: bool = False  # Can we write to this pin for testing?


class GPIOMonitor:
    """
    GPIO Monitor and Control System
    Monitors all GPIO pins and allows control of input pins for testing
    """
    
    def __init__(self, hw_interface, config: Dict):
        """
        Initialize GPIO Monitor
        
        Args:
            hw_interface: Hardware interface instance
            config: System configuration dictionary
        """
        self.hw = hw_interface
        self.config = config
        self.pin_map = self._build_pin_map()
        logger.info("GPIO Monitor initialized")
    
    def _build_pin_map(self) -> Dict[int, PinInfo]:
        """
        Build complete pin mapping from configuration
        
        Based on CG4n51_L2.ino Arduino pins mapped to BCM GPIO:
        Arduino -> RPi BCM
        - pulsos1 (12) -> GPIO 18 (Motor 1 STEP)
        - dir1 (11) -> GPIO 23 (Motor 1 DIR)
        - pulsos2 (10) -> GPIO 24 (Motor 2 STEP)
        - dir2 (9) -> GPIO 25 (Motor 2 DIR)
        - btnReset (22) -> GPIO 17 (Reset/Home Button)
        - btnStart (23) -> GPIO 27 (Start Button)
        - btnStop (24) -> GPIO 22 (Stop Button)
        - btnTala (25) -> GPIO 5 (Tala/Drill Button)
        - switchS (5) -> GPIO 6 (Mode Switch)
        - finHome (3) -> GPIO 13 (Home Limit Switch)
        - finFinal (2) -> GPIO 19 (Final Limit Switch)
        - I2C SDA -> GPIO 2 (RTC)
        - I2C SCL -> GPIO 3 (RTC)
        - ADC via MCP3008 SPI (joystick on channel 0)
        """
        
        pin_map = {}
        
        # Motor outputs (STEP/DIR) - Cannot write to these (controlled by logic)
        pin_map[18] = PinInfo(18, PinType.OUTPUT, PinFunction.MOTOR_STEP, 
                             "Linear STEP", "Linear stage motor step pulses", can_write=False)
        pin_map[23] = PinInfo(23, PinType.OUTPUT, PinFunction.MOTOR_DIR, 
                             "Linear DIR", "Linear stage motor direction", can_write=False)
        pin_map[24] = PinInfo(24, PinType.OUTPUT, PinFunction.MOTOR_STEP, 
                             "Drill STEP", "Drill motor step pulses", can_write=False)
        pin_map[25] = PinInfo(25, PinType.OUTPUT, PinFunction.MOTOR_DIR, 
                             "Drill DIR", "Drill motor direction", can_write=False)
        
        # Button inputs (Active LOW with pull-up) - Can write for testing
        pin_map[17] = PinInfo(17, PinType.INPUT, PinFunction.BUTTON, 
                             "Reset/Home", "Reset/Home button (active LOW)", can_write=True)
        pin_map[27] = PinInfo(27, PinType.INPUT, PinFunction.BUTTON, 
                             "Start", "Start button (active LOW)", can_write=True)
        pin_map[22] = PinInfo(22, PinType.INPUT, PinFunction.BUTTON, 
                             "Stop", "Stop button (active LOW)", can_write=True)
        pin_map[5] = PinInfo(5, PinType.INPUT, PinFunction.BUTTON, 
                            "Tala/Drill", "Tala/Drill button (active LOW)", can_write=True)
        
        # Switches (Active HIGH) - Can write for testing
        pin_map[6] = PinInfo(6, PinType.INPUT, PinFunction.SAFETY_SWITCH, 
                            "Safety Switch", "Safety switch (active HIGH = safe)", can_write=True)
        
        # Limit switches (Active LOW with pull-up) - Can write for testing
        pin_map[13] = PinInfo(13, PinType.INPUT, PinFunction.LIMIT_SWITCH, 
                             "Home Limit", "Home position limit switch (active LOW)", can_write=True)
        pin_map[19] = PinInfo(19, PinType.INPUT, PinFunction.LIMIT_SWITCH, 
                             "Final Limit", "Final position limit switch (active LOW)", can_write=True)
        
        # I2C pins (RTC DS3231) - Cannot write
        pin_map[2] = PinInfo(2, PinType.INPUT, PinFunction.I2C, 
                            "I2C SDA", "I2C Data for RTC DS3231", can_write=False)
        pin_map[3] = PinInfo(3, PinType.INPUT, PinFunction.I2C, 
                            "I2C SCL", "I2C Clock for RTC DS3231", can_write=False)
        
        # SPI pins for MCP3008 ADC (joystick) - Cannot write
        pin_map[8] = PinInfo(8, PinType.OUTPUT, PinFunction.ADC, 
                            "SPI CE0", "SPI Chip Select for MCP3008", can_write=False)
        pin_map[9] = PinInfo(9, PinType.INPUT, PinFunction.ADC, 
                            "SPI MISO", "SPI MISO for MCP3008", can_write=False)
        pin_map[10] = PinInfo(10, PinType.OUTPUT, PinFunction.ADC, 
                             "SPI MOSI", "SPI MOSI for MCP3008", can_write=False)
        pin_map[11] = PinInfo(11, PinType.OUTPUT, PinFunction.ADC, 
                             "SPI SCLK", "SPI Clock for MCP3008", can_write=False)
        
        return pin_map
    
    def get_all_pins_status(self) -> List[Dict]:
        """
        Get status of all configured GPIO pins
        
        Returns:
            List of pin status dictionaries
        """
        status_list = []
        
        for pin_num in sorted(self.pin_map.keys()):
            pin_info = self.pin_map[pin_num]
            
            # Read current value
            try:
                current_value = self.hw.read(pin_num)
            except Exception as e:
                logger.warning(f"Could not read GPIO {pin_num}: {e}")
                current_value = -1  # Unknown
            
            pin_info.current_value = current_value
            
            status_list.append({
                'pin': pin_info.pin,
                'type': pin_info.type.value,
                'function': pin_info.function.value,
                'name': pin_info.name,
                'description': pin_info.description,
                'value': current_value,
                'value_display': 'HIGH' if current_value == 1 else 'LOW' if current_value == 0 else 'UNKNOWN',
                'can_write': pin_info.can_write,
                'is_active': self._is_pin_active(pin_info, current_value)
            })
        
        return status_list
    
    def _is_pin_active(self, pin_info: PinInfo, value: int) -> bool:
        """
        Determine if pin is in 'active' state based on its function
        
        Args:
            pin_info: Pin information
            value: Current pin value
            
        Returns:
            True if pin is active/triggered
        """
        # Buttons and limit switches are active LOW
        if pin_info.function in [PinFunction.BUTTON, PinFunction.LIMIT_SWITCH]:
            return value == 0
        
        # Everything else is active HIGH
        return value == 1
    
    def get_pin_status(self, pin: int) -> Optional[Dict]:
        """
        Get status of a specific pin
        
        Args:
            pin: GPIO pin number
            
        Returns:
            Pin status dictionary or None if pin not found
        """
        if pin not in self.pin_map:
            return None
        
        pin_info = self.pin_map[pin]
        
        try:
            current_value = self.hw.read(pin)
        except Exception as e:
            logger.error(f"Could not read GPIO {pin}: {e}")
            return None
        
        return {
            'pin': pin_info.pin,
            'type': pin_info.type.value,
            'function': pin_info.function.value,
            'name': pin_info.name,
            'description': pin_info.description,
            'value': current_value,
            'value_display': 'HIGH' if current_value == 1 else 'LOW',
            'can_write': pin_info.can_write,
            'is_active': self._is_pin_active(pin_info, current_value)
        }
    
    def write_pin(self, pin: int, value: int) -> Dict:
        """
        Write a value to a GPIO pin (for testing input simulation)
        
        Args:
            pin: GPIO pin number
            value: Value to write (0 or 1)
            
        Returns:
            Dictionary with success status and message
        """
        if pin not in self.pin_map:
            return {
                'success': False,
                'message': f'Pin {pin} is not configured'
            }
        
        pin_info = self.pin_map[pin]
        
        if not pin_info.can_write:
            return {
                'success': False,
                'message': f'Pin {pin} ({pin_info.name}) cannot be written to. '
                          f'It is controlled by the system or is a hardware interface pin.'
            }
        
        if value not in [0, 1]:
            return {
                'success': False,
                'message': f'Invalid value {value}. Must be 0 (LOW) or 1 (HIGH)'
            }
        
        try:
            # For simulation mode, we can directly write to simulate button presses
            self.hw.write(pin, value)
            
            logger.info(f"GPIO {pin} ({pin_info.name}) set to {value} ({'HIGH' if value else 'LOW'}). Saved value is {self.hw.read(pin)}")
            
            return {
                'success': True,
                'message': f'Pin {pin} ({pin_info.name}) set to {"HIGH" if value else "LOW"}',
                'pin': pin,
                'name': pin_info.name,
                'value': value
            }
            
        except Exception as e:
            logger.error(f"Failed to write to GPIO {pin}: {e}")
            return {
                'success': False,
                'message': f'Error writing to pin {pin}: {str(e)}'
            }
    
    def simulate_button_press(self, pin: int, duration_ms: int = 100) -> Dict:
        """
        Simulate a button press (pull LOW then release to HIGH)
        
        Args:
            pin: GPIO pin number of button
            duration_ms: Duration to hold button pressed (milliseconds)
            
        Returns:
            Dictionary with success status and message
        """
        if pin not in self.pin_map:
            return {
                'success': False,
                'message': f'Pin {pin} is not configured'
            }
        
        pin_info = self.pin_map[pin]
        
        if pin_info.function != PinFunction.BUTTON:
            return {
                'success': False,
                'message': f'Pin {pin} ({pin_info.name}) is not a button'
            }
        
        try:
            # Press button (active LOW)
            self.hw.write(pin, 0)
            logger.info(f"Button {pin_info.name} pressed")
            
            # Hold for duration
            time.sleep(duration_ms / 1000.0)
            
            # Release button (pull-up to HIGH)
            self.hw.write(pin, 1)
            logger.info(f"Button {pin_info.name} released")
            
            return {
                'success': True,
                'message': f'Button {pin_info.name} pressed for {duration_ms}ms',
                'pin': pin,
                'name': pin_info.name
            }
            
        except Exception as e:
            logger.error(f"Failed to simulate button press on GPIO {pin}: {e}")
            return {
                'success': False,
                'message': f'Error simulating button press: {str(e)}'
            }
    
    def get_input_pins(self) -> List[Dict]:
        """
        Get list of all input pins that can be written to for testing
        
        Returns:
            List of writable input pin information
        """
        return [
            {
                'pin': pin_info.pin,
                'name': pin_info.name,
                'function': pin_info.function.value,
                'description': pin_info.description
            }
            for pin_info in self.pin_map.values()
            if pin_info.can_write
        ]
    
    def get_pin_groups(self) -> Dict[str, List[Dict]]:
        """
        Get pins organized by functional groups
        
        Returns:
            Dictionary of pin groups
        """
        all_pins = self.get_all_pins_status()
        
        groups = {
            'motors': [p for p in all_pins if p['function'] in ['Motor STEP', 'Motor DIR']],
            'buttons': [p for p in all_pins if p['function'] == 'Button'],
            'switches': [p for p in all_pins if p['function'] in ['Safety Switch', 'Limit Switch']],
            'communication': [p for p in all_pins if p['function'] in ['I2C', 'ADC']]
        }
        
        return groups
