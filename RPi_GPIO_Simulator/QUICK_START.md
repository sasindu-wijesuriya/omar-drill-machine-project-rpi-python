# Quick Start Guide

## Setup (First Time Only)

1. **Install dependencies:**
   ```powershell
   cd "F:\Downloads\Omar Project Python RPi\RPi_GPIO_Simulator"
   pip install -r requirements.txt
   ```

## Running the Simulator

### Step 1: Start the GPIO Simulator

```powershell
cd "F:\Downloads\Omar Project Python RPi\RPi_GPIO_Simulator"
python simulator.py
```

**Expected output:**

```
============================================================
Raspberry Pi GPIO Simulator
Starting on http://localhost:8100
============================================================
INFO:simulator:GPIO Simulator initialized with 11 pins
...
```

### Step 2: Open the Web Interface

Open your browser to: **http://localhost:8100**

You should see:

- Raspberry Pi 40-pin header visualization
- Button controls (Reset, Start, Stop, Tala)
- Limit switch toggles
- Motor output indicators

### Step 3: Test the Simulator (Optional)

In a new terminal:

```powershell
cd "F:\Downloads\Omar Project Python RPi\RPi_GPIO_Simulator"
python mock_gpio/pigpio.py
```

You should see test outputs confirming the simulator is working.

## Integration with Motor Control App

### Option A: Using Mock Library (Recommended)

1. **Edit** `RPi_Motor_Control/main.py` and add at the top:

   ```python
   import sys
   import os

   # Add mock GPIO to path for local testing
   simulator_path = os.path.join(os.path.dirname(__file__), '..', 'RPi_GPIO_Simulator', 'mock_gpio')
   if os.path.exists(simulator_path):
       sys.path.insert(0, simulator_path)
       print(f"✓ Using GPIO Simulator mock library from {simulator_path}")
   ```

2. **Run motor control** (with simulator already running):
   ```powershell
   cd "F:\Downloads\Omar Project Python RPi\RPi_Motor_Control"
   python main.py
   ```

### Option B: Built-in Simulation Mode

1. **Edit** `RPi_Motor_Control/config/system_config.json`:

   ```json
   {
     "system": {
       "simulation_mode": true,
       ...
     }
   }
   ```

2. **Run motor control:**
   ```powershell
   cd "F:\Downloads\Omar Project Python RPi\RPi_Motor_Control"
   python main.py
   ```

## Testing Workflow

1. **Simulator running** on port 8100 → http://localhost:8100
2. **Motor control running** on port 5000 → http://localhost:5000
3. **Test buttons** in simulator UI
4. **Watch outputs** change in real-time
5. **Use motor control** web interface normally

## Common Issues

### Port Already in Use

```powershell
# Find what's using port 8100
netstat -ano | findstr :8100
# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F
```

### Can't Connect

- Ensure simulator is running first
- Check firewall is not blocking port 8100
- Try http://127.0.0.1:8100 instead

### Import Errors

```powershell
pip install -r requirements.txt
```

## Quick Test Commands

**Terminal 1 - Simulator:**

```powershell
cd "F:\Downloads\Omar Project Python RPi\RPi_GPIO_Simulator" ; python simulator.py
```

**Terminal 2 - Motor Control:**

```powershell
cd "F:\Downloads\Omar Project Python RPi\RPi_Motor_Control" ; python main.py
```

**Browser:**

- Simulator: http://localhost:8100
- Motor Control: http://localhost:5000

---

That's it! You now have a fully functional GPIO simulator for local testing.
