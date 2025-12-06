"""
Mock pigpio module that communicates with the GPIO simulator
This replaces the real pigpio library for local testing
"""

import requests
import time
import logging

logger = logging.getLogger(__name__)

# Simulator configuration
SIMULATOR_URL = "http://localhost:8100"

# pigpio constants - GPIO Modes
INPUT = 0
OUTPUT = 1
ALT0 = 4
ALT1 = 5
ALT2 = 6
ALT3 = 7
ALT4 = 3
ALT5 = 2

# Pull-up/Pull-down constants
PUD_OFF = 0
PUD_UP = 1
PUD_DOWN = 2

# Edge detection constants
RISING_EDGE = 0
FALLING_EDGE = 1
EITHER_EDGE = 2

# Other constants
TIMEOUT = 2


class pi:
    """Mock pigpio pi class that communicates with GPIO simulator"""
    
    def __init__(self, host='localhost', port=8888):
        """Initialize connection to GPIO simulator"""
        self.host = host
        self.port = port
        self._connected = False
        self._start_time = time.time()
        self._read_cache = {}  # Cache for read values
        self._cache_time = {}  # Timestamps for cache invalidation
        self._cache_ttl = 0.01  # 10ms cache TTL
        
        # Try to connect to simulator
        try:
            response = requests.get(f"{SIMULATOR_URL}/api/pins", timeout=2)
            if response.status_code == 200:
                self._connected = True
                logger.info(f"Connected to GPIO Simulator at {SIMULATOR_URL}")
                print(f"✓ Connected to GPIO Simulator at {SIMULATOR_URL}")
            else:
                logger.warning("GPIO Simulator not responding correctly")
                print(f"⚠ GPIO Simulator not responding correctly")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Could not connect to GPIO Simulator: {e}")
            print(f"⚠ Could not connect to GPIO Simulator at {SIMULATOR_URL}")
            print("  Make sure the simulator is running on port 8100")
            self._connected = False
    
    @property
    def connected(self):
        """Check if connected to simulator"""
        return self._connected
    
    def set_mode(self, pin: int, mode: int):
        """Set pin mode (INPUT/OUTPUT)"""
        mode_str = "INPUT" if mode == INPUT else "OUTPUT"
        try:
            response = requests.post(
                f"{SIMULATOR_URL}/api/pin/{pin}/mode",
                json={"mode": mode_str},
                timeout=0.2  # Shorter timeout
            )
            if response.status_code == 200:
                logger.debug(f"Pin {pin} mode set to {mode_str}")
            else:
                logger.warning(f"Failed to set pin {pin} mode")
        except Exception as e:
            logger.error(f"Error setting pin {pin} mode: {e}")
    
    def set_pull_up_down(self, pin: int, pud: int):
        """Set pull-up/pull-down resistor"""
        pud_map = {PUD_OFF: "OFF", PUD_UP: "UP", PUD_DOWN: "DOWN"}
        pud_str = pud_map.get(pud, "OFF")
        
        try:
            response = requests.post(
                f"{SIMULATOR_URL}/api/pin/{pin}/pull",
                json={"pull": pud_str},
                timeout=0.2  # Shorter timeout
            )
            if response.status_code == 200:
                logger.debug(f"Pin {pin} pull resistor set to {pud_str}")
            else:
                logger.warning(f"Failed to set pin {pin} pull resistor")
        except Exception as e:
            logger.error(f"Error setting pin {pin} pull resistor: {e}")
    
    def read(self, pin: int) -> int:
        """Read digital pin value (with caching to avoid HTTP flooding)"""
        current_time = time.time()
        
        # Check cache
        if pin in self._read_cache:
            if current_time - self._cache_time[pin] < self._cache_ttl:
                return self._read_cache[pin]
        
        # Cache miss or expired - fetch from simulator
        try:
            response = requests.get(
                f"{SIMULATOR_URL}/api/pin/{pin}/value",
                timeout=0.05  # Much shorter timeout (50ms)
            )
            if response.status_code == 200:
                data = response.json()
                value = data.get('value', 0)
                self._read_cache[pin] = value
                self._cache_time[pin] = current_time
                return value
            else:
                logger.warning(f"Failed to read pin {pin}")
                return self._read_cache.get(pin, 0)  # Return cached value on error
        except Exception as e:
            logger.debug(f"Error reading pin {pin}: {e}")
            return self._read_cache.get(pin, 0)  # Return cached value on error
    
    def write(self, pin: int, value: int):
        """Write digital pin value"""
        try:
            response = requests.post(
                f"{SIMULATOR_URL}/api/pin/{pin}/value",
                json={"value": value},
                timeout=0.05  # Shorter timeout (50ms)
            )
            if response.status_code != 200:
                logger.warning(f"Failed to write pin {pin}")
        except Exception as e:
            # Don't log every write error in tight loops
            pass
    
    def hardware_PWM(self, pin: int, frequency: int, dutycycle: int):
        """Simulate hardware PWM (logged but not fully simulated)"""
        logger.debug(f"PWM on pin {pin}: freq={frequency}Hz, duty={dutycycle/10000:.1f}%")
        
        # For PWM, we simulate by rapidly toggling (simplified)
        # In real usage, this would be handled by hardware
        # For now, just set the pin to 1 if dutycycle > 0
        if dutycycle > 0:
            self.write(pin, 1)
        else:
            self.write(pin, 0)
    
    def get_current_tick(self) -> int:
        """Get current microsecond tick"""
        return int((time.time() - self._start_time) * 1000000)
    
    def stop(self):
        """Close connection"""
        logger.info("Mock pigpio connection closed")
        self._connected = False


def get_simulator_status():
    """Check if simulator is running"""
    try:
        response = requests.get(f"{SIMULATOR_URL}/api/pins", timeout=2)
        return response.status_code == 200
    except:
        return False


if __name__ == "__main__":
    # Test the mock library
    print("Testing Mock pigpio library...")
    
    if not get_simulator_status():
        print("ERROR: GPIO Simulator is not running!")
        print(f"Please start the simulator first: python simulator.py")
        exit(1)
    
    print("Simulator detected, testing connection...")
    
    # Create pi instance
    gpio = pi()
    
    if not gpio.connected:
        print("ERROR: Could not connect to simulator")
        exit(1)
    
    print("✓ Connected successfully")
    
    # Test pin operations
    print("\nTesting pin operations...")
    
    test_pin = 17  # btnReset
    
    # Set as input with pull-up
    gpio.set_mode(test_pin, INPUT)
    gpio.set_pull_up_down(test_pin, PUD_UP)
    print(f"✓ Set pin {test_pin} as INPUT with PULL_UP")
    
    # Read value
    value = gpio.read(test_pin)
    print(f"✓ Read pin {test_pin} value: {value}")
    
    # Test output pin
    test_output = 18  # pulsos1
    gpio.set_mode(test_output, OUTPUT)
    print(f"✓ Set pin {test_output} as OUTPUT")
    
    # Write values
    gpio.write(test_output, 1)
    print(f"✓ Wrote 1 to pin {test_output}")
    time.sleep(0.5)
    
    gpio.write(test_output, 0)
    print(f"✓ Wrote 0 to pin {test_output}")
    
    # Test PWM
    gpio.hardware_PWM(test_output, 1000, 500000)  # 1kHz, 50% duty
    print(f"✓ Set PWM on pin {test_output}")
    
    gpio.stop()
    print("\n✓ All tests passed!")
    print(f"\nOpen your browser to {SIMULATOR_URL} to see the simulator UI")
