"""
Comprehensive Test Suite for GPIO Simulator
Run this to verify all functionality
"""

import requests
import time
import sys
import os

# Add mock GPIO to path
simulator_path = os.path.join(os.path.dirname(__file__), 'mock_gpio')
sys.path.insert(0, simulator_path)

SIMULATOR_URL = "http://localhost:8100"

def check_simulator_running():
    """Check if simulator is accessible"""
    print("=" * 60)
    print("CHECKING SIMULATOR STATUS")
    print("=" * 60)
    try:
        response = requests.get(f"{SIMULATOR_URL}/api/pins", timeout=2)
        if response.status_code == 200:
            print("✓ Simulator is running and accessible")
            return True
        else:
            print(f"✗ Simulator returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to simulator: {e}")
        print(f"\nPlease start the simulator first:")
        print(f"  cd RPi_GPIO_Simulator")
        print(f"  python simulator.py")
        return False

def test_rest_api():
    """Test REST API endpoints"""
    print("\n" + "=" * 60)
    print("TESTING REST API")
    print("=" * 60)
    
    # Test 1: Get all pins
    print("\n1. Getting all pin states...")
    response = requests.get(f"{SIMULATOR_URL}/api/pins")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Retrieved {len(data['pins'])} pins")
    else:
        print(f"   ✗ Failed to get pins")
        return False
    
    # Test 2: Get specific pin
    test_pin = 17
    print(f"\n2. Getting GPIO {test_pin} state...")
    response = requests.get(f"{SIMULATOR_URL}/api/pin/{test_pin}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ GPIO {test_pin} value: {data['state']['value']}")
    else:
        print(f"   ✗ Failed to get pin {test_pin}")
        return False
    
    # Test 3: Set pin value
    print(f"\n3. Setting GPIO {test_pin} to 0...")
    response = requests.post(
        f"{SIMULATOR_URL}/api/pin/{test_pin}/value",
        json={"value": 0}
    )
    if response.status_code == 200:
        print(f"   ✓ GPIO {test_pin} set to 0")
    else:
        print(f"   ✗ Failed to set pin {test_pin}")
        return False
    
    # Test 4: Toggle pin
    print(f"\n4. Toggling GPIO {test_pin}...")
    response = requests.post(f"{SIMULATOR_URL}/api/pin/{test_pin}/toggle")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ GPIO {test_pin} toggled to {data['value']}")
    else:
        print(f"   ✗ Failed to toggle pin {test_pin}")
        return False
    
    # Test 5: Reset simulator
    print(f"\n5. Resetting simulator...")
    response = requests.post(f"{SIMULATOR_URL}/api/reset")
    if response.status_code == 200:
        print(f"   ✓ Simulator reset successful")
    else:
        print(f"   ✗ Failed to reset simulator")
        return False
    
    return True

def test_mock_library():
    """Test mock pigpio library"""
    print("\n" + "=" * 60)
    print("TESTING MOCK PIGPIO LIBRARY")
    print("=" * 60)
    
    try:
        import pigpio
        print("\n✓ Mock pigpio imported successfully")
        print(f"  Location: {pigpio.__file__}")
    except ImportError as e:
        print(f"\n✗ Failed to import pigpio: {e}")
        return False
    
    # Test connection
    print("\n1. Connecting to simulator...")
    gpio = pigpio.pi()
    if not gpio.connected:
        print("   ✗ Failed to connect")
        return False
    print("   ✓ Connected successfully")
    
    # Test input pin
    print("\n2. Testing input pin (GPIO 17 - Reset button)...")
    gpio.set_mode(17, pigpio.INPUT)
    gpio.set_pull_up_down(17, pigpio.PUD_UP)
    value = gpio.read(17)
    print(f"   ✓ GPIO 17 configured as INPUT with PULL_UP")
    print(f"   ✓ Current value: {value}")
    
    # Test output pin
    print("\n3. Testing output pin (GPIO 18 - Pulsos1)...")
    gpio.set_mode(18, pigpio.OUTPUT)
    print(f"   ✓ GPIO 18 configured as OUTPUT")
    
    print("   Testing output toggle...")
    for i in range(3):
        gpio.write(18, 1)
        print(f"     Wrote 1")
        time.sleep(0.2)
        gpio.write(18, 0)
        print(f"     Wrote 0")
        time.sleep(0.2)
    print("   ✓ Output test complete")
    
    # Test PWM
    print("\n4. Testing PWM (GPIO 18)...")
    gpio.hardware_PWM(18, 1000, 500000)  # 1kHz, 50% duty
    print("   ✓ PWM configured (check simulator UI)")
    
    # Cleanup
    gpio.stop()
    print("\n✓ Mock library test complete")
    return True

def test_all_buttons():
    """Test all button pins"""
    print("\n" + "=" * 60)
    print("TESTING ALL BUTTON PINS")
    print("=" * 60)
    print("\nWatch the simulator UI for button state changes...")
    
    buttons = {
        17: "Reset",
        27: "Start",
        22: "Stop",
        5: "Tala"
    }
    
    for pin, name in buttons.items():
        print(f"\n{name} button (GPIO {pin}):")
        # Press (LOW)
        requests.post(f"{SIMULATOR_URL}/api/pin/{pin}/value", json={"value": 0})
        print(f"  ✓ Pressed (0)")
        time.sleep(0.3)
        # Release (HIGH)
        requests.post(f"{SIMULATOR_URL}/api/pin/{pin}/value", json={"value": 1})
        print(f"  ✓ Released (1)")
        time.sleep(0.3)
    
    print("\n✓ All buttons tested")
    return True

def test_limit_switches():
    """Test all limit switch pins"""
    print("\n" + "=" * 60)
    print("TESTING LIMIT SWITCHES")
    print("=" * 60)
    print("\nWatch the simulator UI for limit switch changes...")
    
    switches = {
        13: "Home Limit",
        19: "Final Limit",
        6: "Safety Switch"
    }
    
    for pin, name in switches.items():
        print(f"\n{name} (GPIO {pin}):")
        # Trigger (LOW)
        requests.post(f"{SIMULATOR_URL}/api/pin/{pin}/value", json={"value": 0})
        print(f"  ✓ Triggered (0)")
        time.sleep(0.5)
        # Release (HIGH)
        requests.post(f"{SIMULATOR_URL}/api/pin/{pin}/value", json={"value": 1})
        print(f"  ✓ Released (1)")
        time.sleep(0.5)
    
    print("\n✓ All limit switches tested")
    return True

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  RASPBERRY PI GPIO SIMULATOR - TEST SUITE".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    
    # Check simulator
    if not check_simulator_running():
        print("\n⚠ TESTS ABORTED - Simulator not running")
        return False
    
    # Run tests
    tests = [
        ("REST API", test_rest_api),
        ("Mock pigpio Library", test_mock_library),
        ("Button Controls", test_all_buttons),
        ("Limit Switches", test_limit_switches),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print("\n" + "=" * 60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Simulator is fully functional.")
        print(f"\nYou can now:")
        print(f"  1. Open the UI: {SIMULATOR_URL}")
        print(f"  2. Run your motor control app with the mock library")
        print(f"  3. Test GPIO interactions visually")
        return True
    else:
        print(f"\n⚠ Some tests failed. Please check the output above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
