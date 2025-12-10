# GPIO Monitor & Control System

## Overview

The GPIO Monitor system provides real-time monitoring and control of all GPIO pins used in the RPi Motor Control system. This is essential for testing and debugging hardware connections, simulating button presses, and verifying pin states.

## Features

✅ **Real-time Pin Monitoring**: View the current state of all GPIO pins
✅ **Input Pin Control**: Write HIGH/LOW values to input pins for testing
✅ **Button Simulation**: Simulate button presses with configurable duration
✅ **Web Interface**: User-friendly interface with auto-refresh capability
✅ **REST API**: Full programmatic access via HTTP endpoints
✅ **WebSocket Updates**: Real-time updates when pins change
✅ **Pin Classification**: Organized by function (Motors, Buttons, Switches, Communication)
✅ **Safety**: Only input pins can be written to; motor outputs are read-only

## GPIO Pin Mapping

### Arduino to Raspberry Pi BCM Pin Mapping

Based on the original CG4n51_L2.ino Arduino code:

| Arduino Pin | Function | RPi BCM GPIO | Type | Can Write? |
|-------------|----------|--------------|------|------------|
| 12 | pulsos1 (Linear STEP) | GPIO 18 | OUTPUT | ❌ No |
| 11 | dir1 (Linear DIR) | GPIO 23 | OUTPUT | ❌ No |
| 10 | pulsos2 (Drill STEP) | GPIO 24 | OUTPUT | ❌ No |
| 9 | dir2 (Drill DIR) | GPIO 25 | OUTPUT | ❌ No |
| 22 | btnReset (Home) | GPIO 17 | INPUT | ✅ Yes |
| 23 | btnStart | GPIO 27 | INPUT | ✅ Yes |
| 24 | btnStop | GPIO 22 | INPUT | ✅ Yes |
| 25 | btnTala (Drill) | GPIO 5 | INPUT | ✅ Yes |
| 5 | switchS (Mode) | GPIO 6 | INPUT | ✅ Yes |
| 3 | finHome (Home Limit) | GPIO 13 | INPUT | ✅ Yes |
| 2 | finFinal (Final Limit) | GPIO 19 | INPUT | ✅ Yes |
| - | I2C SDA (RTC) | GPIO 2 | I2C | ❌ No |
| - | I2C SCL (RTC) | GPIO 3 | I2C | ❌ No |
| A0 | Joystick (via MCP3008 ADC) | SPI (GPIO 8-11) | SPI/ADC | ❌ No |

### Pin Groups

**Motor Outputs (Read-Only)**
- GPIO 18, 23, 24, 25: Controlled by motor logic, cannot be written to

**Button Inputs (Writable for Testing)**
- GPIO 17, 27, 22, 5: Active LOW with pull-up resistors
- Can simulate button presses

**Limit Switches (Writable for Testing)**
- GPIO 13, 19: Active LOW with pull-up resistors
- Can simulate limit switch triggers

**Mode Switch (Writable for Testing)**
- GPIO 6: Mode selector

**Communication (Read-Only)**
- GPIO 2, 3: I2C for RTC DS3231
- GPIO 8, 9, 10, 11: SPI for MCP3008 ADC

## Web Interface

### Access

Navigate to: **http://\<your-pi-ip\>:5000/gpio**

Or from the main dashboard, click the **"GPIO Monitor"** button in the navigation.

### Features

1. **Pin Status Display**
   - Organized by functional groups
   - Shows current HIGH/LOW state
   - Visual indicators for active pins
   - Pin descriptions and BCM numbers

2. **Control Buttons**
   - **HIGH/LOW buttons**: Set input pins to specific states
   - **Press button**: Simulate button press (100ms LOW pulse)
   - Buttons are disabled when pin is already in that state

3. **Auto-Refresh**
   - Toggle auto-refresh (updates every 500ms)
   - Manual refresh button
   - Shows last update timestamp

4. **Real-time Updates**
   - WebSocket connection for instant updates
   - Visual feedback when pins change

## REST API Endpoints

### Get All Pin Status

```bash
GET /api/gpio/status
```

**Response:**
```json
{
  "pins": [
    {
      "pin": 17,
      "type": "INPUT",
      "function": "Button",
      "name": "Reset/Home",
      "description": "Reset/Home button (active LOW)",
      "value": 1,
      "value_display": "HIGH",
      "can_write": true,
      "is_active": false
    },
    ...
  ]
}
```

### Get Pin Groups

```bash
GET /api/gpio/groups
```

**Response:**
```json
{
  "motors": [...],
  "buttons": [...],
  "switches": [...],
  "communication": [...]
}
```

### Get Specific Pin Status

```bash
GET /api/gpio/pin/<pin_number>
```

**Example:**
```bash
curl http://localhost:5000/api/gpio/pin/17
```

### Write to Pin

```bash
POST /api/gpio/write
Content-Type: application/json

{
  "pin": 17,
  "value": 1
}
```

**Example:**
```bash
# Set GPIO 17 to HIGH
curl -X POST http://localhost:5000/api/gpio/write \
  -H "Content-Type: application/json" \
  -d '{"pin": 17, "value": 1}'

# Set GPIO 17 to LOW (simulate button press - active LOW)
curl -X POST http://localhost:5000/api/gpio/write \
  -H "Content-Type: application/json" \
  -d '{"pin": 17, "value": 0}'
```

**Response:**
```json
{
  "success": true,
  "message": "Pin 17 (Reset/Home) set to HIGH",
  "pin": 17,
  "name": "Reset/Home",
  "value": 1
}
```

### Simulate Button Press

```bash
POST /api/gpio/button_press
Content-Type: application/json

{
  "pin": 27,
  "duration": 100
}
```

**Example:**
```bash
# Simulate Start button press (100ms)
curl -X POST http://localhost:5000/api/gpio/button_press \
  -H "Content-Type: application/json" \
  -d '{"pin": 27, "duration": 100}'
```

**Response:**
```json
{
  "success": true,
  "message": "Button Start pressed for 100ms",
  "pin": 27,
  "name": "Start"
}
```

### Get Writable Pins

```bash
GET /api/gpio/writable
```

**Response:**
```json
{
  "pins": [
    {
      "pin": 17,
      "name": "Reset/Home",
      "function": "Button",
      "description": "Reset/Home button (active LOW)"
    },
    ...
  ]
}
```

## Python Usage Example

```python
import requests
import time

BASE_URL = "http://localhost:5000"

# Get all pin status
response = requests.get(f"{BASE_URL}/api/gpio/status")
pins = response.json()['pins']
print(f"Found {len(pins)} GPIO pins")

# Simulate Start button press
response = requests.post(
    f"{BASE_URL}/api/gpio/button_press",
    json={"pin": 27, "duration": 100}
)
print(response.json()['message'])

# Set mode switch HIGH
response = requests.post(
    f"{BASE_URL}/api/gpio/write",
    json={"pin": 6, "value": 1}
)
print(response.json()['message'])

# Wait a bit
time.sleep(1)

# Set mode switch LOW
response = requests.post(
    f"{BASE_URL}/api/gpio/write",
    json={"pin": 6, "value": 0}
)
print(response.json()['message'])
```

## Testing Scenarios

### Test Button Inputs

```bash
# Test Reset/Home button (GPIO 17)
curl -X POST http://localhost:5000/api/gpio/button_press \
  -H "Content-Type: application/json" \
  -d '{"pin": 17, "duration": 100}'

# Test Start button (GPIO 27)
curl -X POST http://localhost:5000/api/gpio/button_press \
  -H "Content-Type: application/json" \
  -d '{"pin": 27, "duration": 100}'

# Test Stop button (GPIO 22)
curl -X POST http://localhost:5000/api/gpio/button_press \
  -H "Content-Type: application/json" \
  -d '{"pin": 22, "duration": 100}'

# Test Tala/Drill button (GPIO 5)
curl -X POST http://localhost:5000/api/gpio/button_press \
  -H "Content-Type: application/json" \
  -d '{"pin": 5, "duration": 100}'
```

### Test Limit Switches

```bash
# Trigger Home limit switch (active LOW)
curl -X POST http://localhost:5000/api/gpio/write \
  -H "Content-Type: application/json" \
  -d '{"pin": 13, "value": 0}'

# Release Home limit switch
curl -X POST http://localhost:5000/api/gpio/write \
  -H "Content-Type: application/json" \
  -d '{"pin": 13, "value": 1}'

# Trigger Final limit switch (active LOW)
curl -X POST http://localhost:5000/api/gpio/write \
  -H "Content-Type: application/json" \
  -d '{"pin": 19, "value": 0}'

# Release Final limit switch
curl -X POST http://localhost:5000/api/gpio/write \
  -H "Content-Type: application/json" \
  -d '{"pin": 19, "value": 1}'
```

### Test Mode Switch

```bash
# Set mode switch HIGH
curl -X POST http://localhost:5000/api/gpio/write \
  -H "Content-Type: application/json" \
  -d '{"pin": 6, "value": 1}'

# Set mode switch LOW
curl -X POST http://localhost:5000/api/gpio/write \
  -H "Content-Type: application/json" \
  -d '{"pin": 6, "value": 0}'
```

## Pin States and Logic

### Active LOW Pins (Buttons & Limit Switches)

These pins use pull-up resistors and are active when LOW:

- **Normal state**: HIGH (1) - not pressed/not triggered
- **Active state**: LOW (0) - pressed/triggered

To simulate activation:
```bash
# Activate (press button / trigger switch)
curl -X POST http://localhost:5000/api/gpio/write \
  -H "Content-Type: application/json" \
  -d '{"pin": 17, "value": 0}'

# Deactivate (release button / clear switch)
curl -X POST http://localhost:5000/api/gpio/write \
  -H "Content-Type: application/json" \
  -d '{"pin": 17, "value": 1}'
```

### Motor Outputs (Read-Only)

Motor STEP and DIR pins cannot be written to via the GPIO monitor. These are controlled by the motor logic system. You can only observe their state.

## Safety Features

1. **Write Protection**: Only input pins can be written to
2. **Motor Protection**: Motor output pins are read-only
3. **Validation**: All API requests validate pin numbers and values
4. **Error Handling**: Clear error messages for invalid operations
5. **Logging**: All GPIO operations are logged

## Troubleshooting

### Pin Shows Wrong State

1. Check if the system is in simulation mode (default on non-Raspberry Pi)
2. Verify physical connections if on real hardware
3. Check for pull-up/pull-down resistor configuration

### Cannot Write to Pin

Ensure the pin is writable:
- Only INPUT pins can be written to
- Motor outputs (GPIO 18, 23, 24, 25) are read-only
- Communication pins (I2C, SPI) are read-only

### Web Interface Not Updating

1. Check WebSocket connection (should show "Connected" in browser)
2. Enable auto-refresh mode
3. Check browser console for errors
4. Verify service is running: `sudo systemctl status rpi-motor-control.service`

## Hardware vs Simulation Mode

### Simulation Mode (Default on Ubuntu)

- Uses simulated GPIO pins
- All pins can be read/written
- No actual hardware interaction
- Perfect for testing logic and web interface

### Hardware Mode (On Raspberry Pi)

- Requires pigpiod daemon: `sudo systemctl start pigpiod`
- Actual hardware pin states
- Input pins reflect real button/switch states
- Writing to pins affects actual hardware

To enable hardware mode, edit `config/system_config.json`:
```json
{
  "system": {
    "simulation_mode": false
  }
}
```

## Integration with Motor Control

The GPIO monitor integrates seamlessly with the motor control logic:

1. **Non-Intrusive**: Reading pins doesn't affect motor operation
2. **Testing**: Simulate button presses to trigger logic without physical buttons
3. **Debugging**: Monitor pin states during operation
4. **Development**: Test logic without physical hardware

## Future Enhancements

Potential additions:
- [ ] Pin history/logging
- [ ] PWM duty cycle monitoring for motor outputs
- [ ] Analog value display for ADC channels
- [ ] GPIO waveform capture
- [ ] Pin configuration export/import
