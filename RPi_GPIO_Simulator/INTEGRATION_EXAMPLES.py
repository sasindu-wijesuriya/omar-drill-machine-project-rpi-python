"""
Example: How to integrate the GPIO Simulator with RPi_Motor_Control

This file shows different ways to use the simulator with your motor control project.
"""

# ============================================================================
# OPTION 1: Add Mock GPIO Path at Runtime (RECOMMENDED FOR TESTING)
# ============================================================================
# Add this to the TOP of your RPi_Motor_Control/main.py

import sys
import os

# Add mock GPIO library to path for local testing
simulator_path = os.path.join(os.path.dirname(__file__), '..', 'RPi_GPIO_Simulator', 'mock_gpio')
if os.path.exists(simulator_path):
    sys.path.insert(0, simulator_path)
    print(f"✓ Using GPIO Simulator mock library")
    print(f"  Path: {simulator_path}")
    print(f"  Simulator should be running on http://localhost:8100")
else:
    print(f"⚠ GPIO Simulator not found at {simulator_path}")
    print(f"  Will use built-in simulation mode instead")

# Now import the rest of your modules
from src.hardware_interface import get_hardware_interface
from src.web_server import app
# ... rest of imports


# ============================================================================
# OPTION 2: Environment Variable
# ============================================================================
# Set an environment variable before running your app

# In PowerShell:
# $env:USE_GPIO_SIMULATOR = "1"
# python main.py

# In your main.py:
if os.environ.get('USE_GPIO_SIMULATOR') == '1':
    simulator_path = os.path.join(os.path.dirname(__file__), '..', 'RPi_GPIO_Simulator', 'mock_gpio')
    sys.path.insert(0, simulator_path)


# ============================================================================
# OPTION 3: Standalone Test Script
# ============================================================================
# Create a test file: RPi_Motor_Control/test_with_simulator.py

"""
Test script for motor control with GPIO simulator
"""
import sys
import os
import time

# Add mock GPIO
simulator_path = os.path.join(os.path.dirname(__file__), '..', 'RPi_GPIO_Simulator', 'mock_gpio')
sys.path.insert(0, simulator_path)

# Import pigpio (will use mock)
import pigpio

# Test basic operations
def test_gpio():
    print("Testing GPIO Simulator...")
    
    # Connect to simulator
    gpio = pigpio.pi()
    
    if not gpio.connected:
        print("ERROR: Could not connect to GPIO Simulator")
        print("Make sure simulator is running: python simulator.py")
        return
    
    print("✓ Connected to GPIO Simulator")
    
    # Test input pin (button)
    button_pin = 17  # Reset button
    gpio.set_mode(button_pin, pigpio.INPUT)
    gpio.set_pull_up_down(button_pin, pigpio.PUD_UP)
    
    print(f"\nReading button (GPIO {button_pin})...")
    print("Click the Reset button in the simulator UI")
    
    for i in range(10):
        value = gpio.read(button_pin)
        print(f"  Button value: {value} {'(PRESSED)' if value == 0 else '(Released)'}")
        time.sleep(0.5)
    
    # Test output pin (motor)
    output_pin = 18  # Pulsos1
    gpio.set_mode(output_pin, pigpio.OUTPUT)
    
    print(f"\nTesting output (GPIO {output_pin})...")
    print("Watch the Motor 1 Pulsos1 LED in simulator UI")
    
    for i in range(5):
        gpio.write(output_pin, 1)
        print(f"  Output: HIGH")
        time.sleep(0.5)
        
        gpio.write(output_pin, 0)
        print(f"  Output: LOW")
        time.sleep(0.5)
    
    gpio.stop()
    print("\n✓ Test complete!")

if __name__ == '__main__':
    test_gpio()


# ============================================================================
# OPTION 4: Using REST API Directly
# ============================================================================
# You can also control the simulator directly via HTTP requests

import requests

SIMULATOR_URL = "http://localhost:8100"

def control_via_api():
    # Get all pin states
    response = requests.get(f"{SIMULATOR_URL}/api/pins")
    pins = response.json()
    print("Current pin states:", pins)
    
    # Set a pin value
    response = requests.post(
        f"{SIMULATOR_URL}/api/pin/17/value",
        json={"value": 0}  # Press button (LOW)
    )
    print("Button pressed:", response.json())
    
    # Read a pin value
    response = requests.get(f"{SIMULATOR_URL}/api/pin/17/value")
    print("Button state:", response.json())
    
    # Toggle a pin
    response = requests.post(f"{SIMULATOR_URL}/api/pin/17/toggle")
    print("Button toggled:", response.json())
    
    # Reset simulator
    response = requests.post(f"{SIMULATOR_URL}/api/reset")
    print("Simulator reset:", response.json())


# ============================================================================
# OPTION 5: Conditional Import Based on System
# ============================================================================
# Add this to hardware_interface.py or main.py

import platform

def setup_gpio():
    if platform.system() == 'Windows':
        # On Windows, use simulator
        simulator_path = os.path.join(os.path.dirname(__file__), '..', 'RPi_GPIO_Simulator', 'mock_gpio')
        if os.path.exists(simulator_path):
            sys.path.insert(0, simulator_path)
            print("✓ Running on Windows - Using GPIO Simulator")
    elif platform.system() == 'Linux':
        # On Linux, check if it's a Raspberry Pi
        try:
            with open('/proc/cpuinfo', 'r') as f:
                if 'Raspberry Pi' in f.read():
                    print("✓ Running on Raspberry Pi - Using real GPIO")
                else:
                    print("⚠ Running on Linux but not RPi - Using simulation")
        except:
            pass


# ============================================================================
# USAGE WORKFLOW
# ============================================================================

"""
COMPLETE TESTING WORKFLOW:

1. Terminal 1 - Start GPIO Simulator:
   cd "F:\Downloads\Omar Project Python RPi\RPi_GPIO_Simulator"
   python simulator.py
   
2. Browser - Open Simulator UI:
   http://localhost:8100
   
3. Terminal 2 - Run Motor Control (with mock):
   cd "F:\Downloads\Omar Project Python RPi\RPi_Motor_Control"
   # Add the path insertion code to main.py first
   python main.py
   
4. Browser - Open Motor Control UI:
   http://localhost:5000
   
5. Test Interaction:
   - Click "Start" button in simulator (port 8100)
   - Watch motor control app respond
   - Use motor control web UI (port 5000)
   - See GPIO outputs in simulator
   - Test limit switches
   - Monitor activity log

BENEFITS:
✓ No Raspberry Pi hardware needed
✓ Safe testing without risk of hardware damage
✓ Visual feedback of all GPIO states
✓ Easy to simulate error conditions
✓ Fast development iteration
✓ Test on Windows/Mac/Linux
"""

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
COMMON ISSUES AND SOLUTIONS:

1. ImportError: No module named 'pigpio'
   Solution: Make sure mock_gpio path is added BEFORE importing pigpio
   
2. Connection refused to localhost:8100
   Solution: Start the simulator first: python simulator.py
   
3. Mock library not being used
   Solution: Check that sys.path.insert happens before any imports
   
4. WebSocket connection failed
   Solution: Refresh browser page (Ctrl+F5)
   
5. Pins not updating in UI
   Solution: Check browser console (F12) for errors

TEST IF MOCK IS BEING USED:
Add this after your imports:
   import pigpio
   print(f"Using pigpio from: {pigpio.__file__}")
   
If it shows the mock_gpio path, you're good!
"""
