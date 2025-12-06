# Raspberry Pi GPIO Simulator

A web-based GPIO simulator for testing Raspberry Pi applications locally on your development PC. This simulator provides a visual interface to interact with GPIO pins and allows you to test your RPi_Motor_Control project without actual hardware.

## 🎯 Features

- **Visual GPIO Interface**: Interactive 40-pin Raspberry Pi header display
- **Real-time Updates**: WebSocket-based live pin state updates
- **Input Simulation**:
  - Button controls (Reset, Start, Stop, Tala)
  - Limit switches (Home, Final, Safety)
  - Manual GPIO toggling
- **Output Monitoring**: Real-time visualization of motor control outputs
- **REST API**: Full GPIO control via HTTP endpoints
- **Mock pigpio Library**: Drop-in replacement for the real pigpio library

## 📋 Prerequisites

- Python 3.7+
- pip (Python package manager)

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
cd "F:\Downloads\Omar Project Python RPi\RPi_GPIO_Simulator"
pip install -r requirements.txt
```

### 2. Start the Simulator

```powershell
python simulator.py
```

The simulator will start on **http://localhost:8100**

### 3. Open the Web Interface

Open your web browser and navigate to:

```
http://localhost:8100
```

You should see the GPIO simulator with the Raspberry Pi 40-pin header and control panel.

### 4. Test the Mock GPIO Library (Optional)

```powershell
python mock_gpio/pigpio.py
```

This will run a test to verify the mock library can communicate with the simulator.

## 🔗 Integration with RPi_Motor_Control

There are **two ways** to integrate the simulator with your motor control project:

### Method 1: Using Mock pigpio Library (Recommended for Testing)

1. **Add mock_gpio to Python path** in your motor control project's `main.py`:

```python
import sys
import os

# Add mock GPIO library to path BEFORE other imports
simulator_path = os.path.join(os.path.dirname(__file__), '..', 'RPi_GPIO_Simulator', 'mock_gpio')
sys.path.insert(0, simulator_path)

# Now import the rest of your modules
from src.hardware_interface import get_hardware_interface
# ... rest of imports
```

2. **Run the simulator first**:

```powershell
cd "F:\Downloads\Omar Project Python RPi\RPi_GPIO_Simulator"
python simulator.py
```

3. **Then run your motor control application** (in a new terminal):

```powershell
cd "F:\Downloads\Omar Project Python RPi\RPi_Motor_Control"
python main.py
```

The motor control app will automatically use the mock pigpio library which communicates with the simulator via HTTP.

### Method 2: Using Built-in Simulation Mode

Your RPi_Motor_Control project already has a simulation mode. Simply ensure:

1. **Simulator is running** on port 8100
2. **Set simulation mode** in `RPi_Motor_Control/config/system_config.json`:

```json
{
  "system": {
    "simulation_mode": true,
    ...
  }
}
```

3. **Run your application**:

```powershell
cd "F:\Downloads\Omar Project Python RPi\RPi_Motor_Control"
python main.py
```

The built-in simulation mode is independent, but you can use the simulator's web UI to visualize and manually control GPIO states.

## 🎮 Using the Simulator

### Input Controls

#### Buttons (Active LOW with Pull-up)

- **Reset Button (GPIO 17)**: Click and hold to simulate pressing
- **Start Button (GPIO 27)**: Click and hold to simulate pressing
- **Stop Button (GPIO 22)**: Click and hold to simulate pressing
- **Tala Button (GPIO 5)**: Click and hold to simulate pressing

When pressed, these buttons go LOW (0). When released, they return to HIGH (1) due to pull-up resistors.

#### Limit Switches (Active LOW with Pull-up)

- **Home Limit (GPIO 13)**: Toggle to simulate limit switch activation
- **Final Limit (GPIO 19)**: Toggle to simulate limit switch activation
- **Safety Switch (GPIO 6)**: Toggle to simulate safety switch state

Toggle ON = Switch triggered (LOW/0), Toggle OFF = Switch released (HIGH/1)

### Output Monitoring

The right panel shows motor control outputs:

- **Motor 1 (Linear)**: Pulsos1 (GPIO 18) and Dir1 (GPIO 23)
- **Motor 2 (Taladro)**: Pulsos2 (GPIO 24) and Dir2 (GPIO 25)

LED indicators light up when outputs are HIGH.

### GPIO Pin Grid

The left panel shows the complete 40-pin header:

- **Green border**: Input pins
- **Red border**: Output pins
- **Yellow glow**: HIGH state (1)
- **Dark**: LOW state (0)

Click any input pin to toggle its value.

## 🔌 API Reference

### Get All Pins

```http
GET /api/pins
```

Returns all pin states.

### Get Pin State

```http
GET /api/pin/{pin}
```

Returns state of specific pin.

### Set Pin Mode

```http
POST /api/pin/{pin}/mode
Content-Type: application/json

{
  "mode": "INPUT" | "OUTPUT"
}
```

### Set Pull Resistor

```http
POST /api/pin/{pin}/pull
Content-Type: application/json

{
  "pull": "OFF" | "UP" | "DOWN"
}
```

### Set Pin Value

```http
POST /api/pin/{pin}/value
Content-Type: application/json

{
  "value": 0 | 1
}
```

### Toggle Input Pin

```http
POST /api/pin/{pin}/toggle
```

### Reset Simulator

```http
POST /api/reset
```

## 🔧 Configuration

### Pin Mappings (from RPi_Motor_Control)

**Motor Outputs:**

- GPIO 18: Pulsos1 (Step pulses for motor 1)
- GPIO 23: Dir1 (Direction for motor 1)
- GPIO 24: Pulsos2 (Step pulses for motor 2)
- GPIO 25: Dir2 (Direction for motor 2)

**Input Buttons:**

- GPIO 17: btnReset
- GPIO 27: btnStart
- GPIO 22: btnStop
- GPIO 5: btnTala

**Limit Switches:**

- GPIO 13: finHome (Home position limit)
- GPIO 19: finFinal (Final position limit)
- GPIO 6: switchS (Safety switch)

### Changing Simulator Port

Edit `simulator.py`:

```python
socketio.run(app, host='0.0.0.0', port=8100, debug=True)
```

Also update `mock_gpio/pigpio.py`:

```python
SIMULATOR_URL = "http://localhost:8100"
```

## 📁 Project Structure

```
RPi_GPIO_Simulator/
├── simulator.py              # Main Flask application
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── mock_gpio/               # Mock pigpio library
│   ├── __init__.py
│   └── pigpio.py           # Mock implementation
├── static/
│   ├── css/
│   │   └── style.css       # Simulator styling
│   └── js/
│       └── main.js         # Client-side logic
└── templates/
    └── index.html          # Main UI template
```

## 🐛 Troubleshooting

### Simulator Won't Start

**Error**: "Address already in use"

- Another application is using port 8100
- Kill the process or change the port in `simulator.py`

### Motor Control App Can't Connect

**Error**: "Could not connect to GPIO Simulator"

- Ensure simulator is running: `python simulator.py`
- Check firewall settings
- Verify port 8100 is accessible

### Mock Library Not Working

**Solution**:

```powershell
# Test mock library independently
cd "F:\Downloads\Omar Project Python RPi\RPi_GPIO_Simulator"
python mock_gpio/pigpio.py
```

If this fails, ensure:

1. Simulator is running
2. `requests` library is installed: `pip install requests`

### WebSocket Connection Issues

- Check browser console for errors (F12)
- Ensure Socket.IO CDN is accessible
- Try refreshing the page (Ctrl+F5)

## 🔄 Workflow Example

**Complete testing workflow:**

1. **Start Simulator** (Terminal 1):

```powershell
cd "F:\Downloads\Omar Project Python RPi\RPi_GPIO_Simulator"
python simulator.py
```

2. **Open Simulator UI** in browser:

```
http://localhost:8100
```

3. **Start Motor Control App** (Terminal 2):

```powershell
cd "F:\Downloads\Omar Project Python RPi\RPi_Motor_Control"
python main.py
```

4. **Access Motor Control UI**:

```
http://localhost:5000
```

5. **Test Workflow**:
   - In simulator (port 8100): Click "Start" button
   - In motor control UI (port 5000): Monitor system response
   - Watch GPIO outputs change in simulator
   - Use limit switches to test safety features

## 📝 Notes

- The simulator is for **development and testing only**
- It simulates digital I/O and basic PWM (simplified)
- Timing may not exactly match real hardware
- ADC (analog input) simulation not yet implemented

## 🆘 Support

For issues or questions:

1. Check the Activity Log in the simulator UI
2. Review browser console (F12) for errors
3. Check terminal output for both simulator and motor control app

## 📜 License

This simulator is part of Omar's Drill Machine Project.

---

**Happy Testing! 🍓🔧**
