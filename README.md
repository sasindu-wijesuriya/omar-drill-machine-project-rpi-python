# RPi Motor Control System - User Guide

A dual-logic motor control system for CNC drill operations with web interface.

## 📋 Prerequisites

- Raspberry Pi (tested on RPi 3/4)
- Raspberry Pi OS (Raspbian) installed
- Internet connection for initial setup
- Two stepper motors with drivers
- MCP3008 ADC chip (for joystick)
- Buttons, switches, and limit switches as per wiring diagram

---

## 🔌 Hardware Wiring

### GPIO Pin Connections

| Component | GPIO Pin | BCM Pin # | Notes |
|-----------|----------|-----------|-------|
| **Motor 1 (Linear)** | | | |
| Pulse/Step | GPIO 18 | 18 | To motor driver STEP |
| Direction | GPIO 23 | 23 | To motor driver DIR |
| **Motor 2 (Drill)** | | | |
| Pulse/Step | GPIO 24 | 24 | To motor driver STEP |
| Direction | GPIO 25 | 25 | To motor driver DIR |
| **Control Buttons** | | | |
| Reset Button | GPIO 17 | 17 | Connect to GND when pressed |
| Start Button | GPIO 27 | 27 | Connect to GND when pressed |
| Stop Button | GPIO 22 | 22 | Connect to GND when pressed |
| Drill Button | GPIO 5 | 5 | Connect to GND when pressed |
| **Safety & Limits** | | | |
| Safety Switch | GPIO 6 | 6 | Active LOW (safe when HIGH) |
| Home Limit Switch | GPIO 13 | 13 | Connect to GND when triggered |
| End Limit Switch | GPIO 19 | 19 | Connect to GND when triggered |
| **Joystick (Manual Control)** | | | |
| Joystick Analog | MCP3008 CH0 | - | See MCP3008 wiring below |

### MCP3008 ADC Wiring (for Joystick)

| MCP3008 Pin | Connect To | Notes |
|-------------|------------|-------|
| VDD (Pin 16) | 3.3V | Power supply |
| VREF (Pin 15) | 3.3V | Reference voltage |
| AGND (Pin 14) | GND | Analog ground |
| CLK (Pin 13) | GPIO 11 (SCLK) | SPI clock |
| DOUT (Pin 12) | GPIO 9 (MISO) | SPI data out |
| DIN (Pin 11) | GPIO 10 (MOSI) | SPI data in |
| CS (Pin 10) | GPIO 8 (CE0) | Chip select |
| DGND (Pin 9) | GND | Digital ground |
| CH0 (Pin 1) | Joystick Analog Output | Joystick Y-axis |

### Joystick Wiring

| Joystick Pin | Connect To |
|--------------|------------|
| VCC | 3.3V |
| GND | GND |
| VRy (Y-axis) | MCP3008 CH0 (Pin 1) |

### Button/Switch Wiring Notes

- All buttons are **active LOW** (connect button between GPIO and GND)
- Add 10kΩ pull-up resistors on all button/switch inputs
- Safety switch must be HIGH (3.3V) for safe operation
- Limit switches trigger when connected to GND

### Stepper Motor Driver Connections

Each motor driver (e.g., A4988, DRV8825) needs:
- **STEP** → GPIO pulse pin (18 for Motor 1, 24 for Motor 2)
- **DIR** → GPIO direction pin (23 for Motor 1, 25 for Motor 2)
- **ENABLE** → GND (always enabled) or GPIO if you want control
- **VDD** → 3.3V (logic supply)
- **VMOT** → Motor power supply (12V-24V depending on your motors)
- **GND** → Common ground with Raspberry Pi

---

## 🚀 Quick Installation (3 Commands)

```bash
# 1. Install dependencies and setup
cd /home/pi/omar-drill-machine-project-rpi-python/RPi_Motor_Control
sudo bash scripts/install.sh

# 2. Install as system service
sudo cp rpi-motor-control.service /etc/systemd/system/
sudo systemctl enable rpi-motor-control.service
sudo systemctl start rpi-motor-control.service

# 3. Check if running
sudo systemctl status rpi-motor-control.service
```

**That's it!** The system will now start automatically on boot.

---

## 🌐 Accessing the Web Interface

### From the Raspberry Pi itself:
```
http://localhost:5000
```

### From another computer on the same network:
```
http://[RASPBERRY-PI-IP]:5000
```

**To find your Raspberry Pi's IP address:**
```bash
hostname -I
```
Example: `http://192.168.1.100:5000`

---

## 📱 Web Interface Guide

### 1. **Main Dashboard** (`/`)
- Select Logic A or Logic B
- Choose operation mode (1-5)
- Start/Stop execution
- Manual mode with joystick control
- Emergency stop button

### 2. **Engineer Menu** (`/engineer`)
- **Password:** `1234` (change in `config/system_config.json`)
- Configure parameters for each mode
- Adjust speeds, steps, and cycle settings
- Save changes (system will stop and reload)

### 3. **Logs Viewer** (`/logs`)
- View system operations log
- Check parameter changes
- Review error history

### 4. **GPIO Monitor** (`/gpio`)
- Real-time status of all GPIO pins
- Monitor buttons and switches
- Debug hardware connections

---

## ⚙️ Configuration Files

Located in `RPi_Motor_Control/config/`:

- **`config_logic_a.json`** - Logic A parameters (CG4n51_L1)
- **`config_logic_b.json`** - Logic B parameters (CG4n51_L2 with RTC)
- **`system_config.json`** - System settings and passwords

**Note:** Configuration changes made through the web interface are automatically saved to these files.

---

## 🔧 System Control Commands

```bash
# Start the service
sudo systemctl start rpi-motor-control.service

# Stop the service
sudo systemctl stop rpi-motor-control.service

# Restart the service
sudo systemctl restart rpi-motor-control.service

# Check service status
sudo systemctl status rpi-motor-control.service

# View live logs
sudo journalctl -u rpi-motor-control.service -f

# View recent errors
sudo journalctl -u rpi-motor-control.service -p err -n 50
```

---

## 🛡️ Safety Features

1. **Safety Switch (GPIO 6):**
   - Must be HIGH (3.3V) for system to operate
   - Automatically stops all motors when triggered
   - System will not start if safety switch is active

2. **Emergency Stop:**
   - Available on web interface
   - Immediately halts all motor operations
   - Requires logic re-selection to restart

3. **Limit Switches:**
   - Home limit (GPIO 13) - Reference position
   - End limit (GPIO 19) - Maximum travel
   - Automatically stops motors at limits

4. **Manual Mode Override:**
   - Stop button (GPIO 22) exits manual mode
   - Safety switch takes priority over all operations

---

## 🐛 Troubleshooting

### Service won't start
```bash
# Check for errors
sudo journalctl -u rpi-motor-control.service -n 50

# Test Python environment
cd /home/pi/omar-drill-machine-project-rpi-python/RPi_Motor_Control
source venv/bin/activate
python main.py
```

### Can't access web interface
```bash
# Check if service is running
sudo systemctl status rpi-motor-control.service

# Check if port 5000 is listening
sudo netstat -tulpn | grep 5000

# Check firewall (if enabled)
sudo ufw allow 5000
```

### Motors not moving
1. Check safety switch is HIGH (GPIO 6 = 3.3V)
2. Verify motor driver power supply is connected
3. Check motor driver enable pins are LOW (enabled)
4. View GPIO monitor in web interface to verify pin states

### Joystick not working
1. Enable SPI: `sudo raspi-config` → Interface Options → SPI → Enable
2. Verify MCP3008 wiring (see table above)
3. Test SPI communication: `ls /dev/spidev*` should show `/dev/spidev0.0`

### Parameters not saving
- Ensure you're logged into Engineer Menu
- Check disk space: `df -h`
- Verify file permissions: `ls -la config/`

---

## 📊 Operation Logs

Logs are stored in `RPi_Motor_Control/logs/`:

- **`operations_YYYYMMDD.csv`** - System operations and state changes
- **`parameters_YYYYMMDD.csv`** - Parameter modification history
- **`errors_YYYYMMDD.csv`** - Error and warning log

Logs automatically rotate daily.

---

## 🔐 Changing Engineer Password

Edit `config/system_config.json`:
```json
{
  "engineer_password": "your-new-password-here"
}
```

Then restart the service:
```bash
sudo systemctl restart rpi-motor-control.service
```

---

## 📞 Support & Documentation

- **Arduino Reference:** See `CG4n51_L1/` and `CG4n51_L2/` folders for original logic
- **System Logs:** `sudo journalctl -u rpi-motor-control.service`
- **Configuration Guides:** See `RPi_Motor_Control/*.md` files

---

## ⚡ Quick Start Checklist

- [ ] All hardware wired according to diagram
- [ ] MCP3008 connected for joystick (SPI enabled)
- [ ] Safety switch installed and in SAFE position (HIGH)
- [ ] Motor drivers powered and enabled
- [ ] System service installed and enabled
- [ ] Web interface accessible at `http://[IP]:5000`
- [ ] Emergency stop button tested
- [ ] Manual mode tested with joystick
- [ ] Limit switches tested (optional but recommended)

**You're ready to operate!** 🎉

---

## 🏗️ System Architecture

- **Logic A (CG4n51_L1):** Standard 5-mode motor control
- **Logic B (CG4n51_L2):** Enhanced with RTC date lockout
- **Web Interface:** Flask + SocketIO for real-time updates
- **Hardware Control:** GPIO via RPi.GPIO + software PWM
- **Configuration:** JSON-based with hot-reload support
- **Logging:** CSV files + systemd journal

---

**Version:** 1.0  
**Last Updated:** December 2025  
