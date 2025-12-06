# GPIO Simulator - Project Summary

## ✅ What Was Created

A complete **Raspberry Pi GPIO Simulator** that allows you to test your RPi_Motor_Control project locally on your Windows PC without needing actual Raspberry Pi hardware.

## 📁 Project Location

```
F:\Downloads\Omar Project Python RPi\RPi_GPIO_Simulator\
```

## 🎯 Key Features

### 1. **Web-Based UI (Port 8100)**

- Visual representation of Raspberry Pi 40-pin header
- Interactive button controls (Reset, Start, Stop, Tala)
- Limit switch toggles (Home, Final, Safety)
- Real-time motor output monitoring
- Activity log showing all GPIO events

### 2. **Mock pigpio Library**

- Drop-in replacement for real pigpio
- Communicates with simulator via HTTP REST API
- Can be used by your motor control project

### 3. **Real-Time Updates**

- WebSocket-based live updates
- Instant reflection of GPIO state changes
- Bi-directional communication

## 🚀 How to Use

### Quick Start

**Terminal 1 - Start Simulator:**

```powershell
cd "F:\Downloads\Omar Project Python RPi\RPi_GPIO_Simulator"
python simulator.py
```

**Browser:**
Open http://localhost:8100

### Testing with Motor Control

**Option 1: Use Mock Library (Recommended)**

1. Start the simulator (port 8100)
2. Add this to the top of `RPi_Motor_Control/main.py`:

   ```python
   import sys
   import os

   # Use simulator for local testing
   simulator_path = os.path.join(os.path.dirname(__file__), '..', 'RPi_GPIO_Simulator', 'mock_gpio')
   if os.path.exists(simulator_path):
       sys.path.insert(0, simulator_path)
   ```

3. Run your motor control app (port 5000)
4. Control GPIO from simulator UI

**Option 2: Built-in Simulation**

1. Start simulator (port 8100)
2. Set `"simulation_mode": true` in motor control config
3. Run motor control app (port 5000)
4. Use simulator UI to visualize and manually control pins

## 📂 Project Structure

```
RPi_GPIO_Simulator/
├── simulator.py                 # Main Flask server (port 8100)
├── requirements.txt             # Python dependencies
├── start_simulator.bat          # Windows shortcut to start
├── README.md                    # Full documentation
├── QUICK_START.md              # Quick reference guide
├── .gitignore                  # Git ignore rules
│
├── mock_gpio/                  # Mock pigpio library
│   ├── __init__.py
│   └── pigpio.py              # Communicates with simulator
│
├── static/                     # Web assets
│   ├── css/
│   │   └── style.css         # Modern dark theme
│   └── js/
│       └── main.js           # Client-side logic
│
└── templates/
    └── index.html            # Main UI page
```

## 🎮 UI Controls

### Input Simulation

- **Buttons**: Click and hold to press (goes LOW), release for HIGH

  - GPIO 17: Reset
  - GPIO 27: Start
  - GPIO 22: Stop
  - GPIO 5: Tala

- **Limit Switches**: Toggle switches
  - GPIO 13: Home Limit
  - GPIO 19: Final Limit
  - GPIO 6: Safety Switch

### Output Monitoring

- **Motor 1 (Linear)**

  - GPIO 18: Pulsos1 (step pulses)
  - GPIO 23: Dir1 (direction)

- **Motor 2 (Taladro)**
  - GPIO 24: Pulsos2 (step pulses)
  - GPIO 25: Dir2 (direction)

## 🔌 API Endpoints

- `GET /api/pins` - Get all pin states
- `GET /api/pin/{pin}` - Get specific pin state
- `POST /api/pin/{pin}/mode` - Set pin mode (INPUT/OUTPUT)
- `POST /api/pin/{pin}/pull` - Set pull resistor (OFF/UP/DOWN)
- `POST /api/pin/{pin}/value` - Set pin value (0/1)
- `POST /api/pin/{pin}/toggle` - Toggle input pin
- `POST /api/reset` - Reset all pins

## ✨ Benefits

1. **No Hardware Required**: Test on your PC without Raspberry Pi
2. **Visual Feedback**: See GPIO states in real-time
3. **Easy Testing**: Click buttons instead of wiring hardware
4. **Safe Development**: No risk of hardware damage
5. **Fast Iteration**: Instant testing without deploy cycles

## 📝 Next Steps

1. ✅ Simulator is already running on port 8100
2. ✅ Web UI is accessible in your browser
3. 📋 To integrate with motor control:
   - Either add mock library path to main.py (Option 1)
   - Or just use built-in simulation mode (Option 2)
4. 🧪 Test your motor control logic safely

## 🆘 Troubleshooting

### Simulator won't start

```powershell
# Check if port 8100 is in use
netstat -ano | findstr :8100
```

### Can't connect from motor control

- Ensure simulator is running first
- Check firewall settings
- Try http://127.0.0.1:8100

### Import errors

```powershell
pip install -r requirements.txt
```

## 📚 Documentation

- **README.md**: Complete documentation with all details
- **QUICK_START.md**: Quick reference for common tasks
- **This file**: High-level summary

## 🎉 Status

✅ **Fully Functional and Ready to Use!**

The simulator is currently running and you can start testing immediately!

---

**Created for Omar's Drill Machine Project**
GPIO Simulator v1.0 - December 2025
