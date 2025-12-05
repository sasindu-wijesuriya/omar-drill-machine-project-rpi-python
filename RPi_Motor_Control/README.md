# RPi Motor Control System

Complete Raspberry Pi motor control system with dual logic modes, web interface, RTC integration, and CSV logging. Migrated from Arduino CG4n51_L1 and CG4n51_L2 programs.

## Features

- **Dual Logic System**: Switch between Logic A (standard control) and Logic B (RTC-based lockout)
- **Web Interface**: Full-featured dashboard accessible via WiFi
- **WiFi Access Point**: Built-in hotspot mode for standalone operation
- **Real-time Status**: WebSocket-based live updates
- **CSV Logging**: Automatic logging of operations, parameters, and errors
- **RTC Integration**: DS3231 Real-Time Clock for date-based features
- **Engineer Menu**: Password-protected parameter adjustment
- **Simulation Mode**: Test without hardware

## Hardware Requirements

### Required Components

- **Raspberry Pi**: 3B+ or 4 (1GB+ RAM recommended)
- **Stepper Motors**: 2x with STEP/DIR drivers
- **DS3231 RTC Module**: I2C interface (0x68)
- **MCP3008 ADC**: For analog joystick (SPI)
- **Power Supply**: 5V 3A for Pi + motor driver supply

### Control Inputs

- 4x Push Buttons: Reset, Start, Stop, Tala
- 1x Toggle Switch: Mode selector
- 2x Limit Switches: Home and final position
- 1x Analog Joystick: Manual control (X-axis)

## Pin Mapping

### GPIO Pinout (BCM Mode)

```
Motor 1:
  - STEP: GPIO 18
  - DIR:  GPIO 23

Motor 2:
  - STEP: GPIO 24
  - DIR:  GPIO 25

Buttons:
  - Reset: GPIO 17
  - Start: GPIO 27
  - Stop:  GPIO 22
  - Tala:  GPIO 5

Switches:
  - Mode:       GPIO 6
  - Limit Home: GPIO 13
  - Limit Final: GPIO 19

I2C (RTC):
  - SDA: GPIO 2
  - SCL: GPIO 3

SPI (ADC):
  - MOSI: GPIO 10
  - MISO: GPIO 9
  - CLK:  GPIO 11
  - CS0:  GPIO 8
```

## Installation

### Quick Install (Recommended)

```bash
# 1. Clone repository to /home/pi
cd /home/pi
git clone <your-repo> RPi_Motor_Control
cd RPi_Motor_Control

# 2. Run installation script
sudo bash scripts/install.sh

# 3. Setup WiFi Access Point (optional)
sudo bash scripts/setup_wifi_ap.sh
sudo reboot
```

### Manual Installation

```bash
# 1. Update system
sudo apt-get update
sudo apt-get upgrade -y

# 2. Install dependencies
sudo apt-get install -y python3 python3-pip python3-venv i2c-tools pigpio

# 3. Enable interfaces
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

# 4. Start pigpio daemon
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

# 5. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 6. Install Python packages
pip install -r requirements.txt
```

### Development (Simulation Mode)

```bash
cd RPi_Motor_Control
pip install -r requirements.txt
python main.py --simulate
```

## Usage

### Running the System

**Test Mode (Simulation):**

```bash
source venv/bin/activate
python main.py --simulate
```

**Production Mode:**

```bash
source venv/bin/activate
python main.py
```

**With Debug Logging:**

```bash
python main.py --debug
```

**Custom Port:**

```bash
python main.py --port 8080
```

### Auto-Start on Boot

```bash
# Install service
sudo cp scripts/motor_control.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable motor_control
sudo systemctl start motor_control

# Check status
sudo systemctl status motor_control

# View logs
sudo journalctl -u motor_control -f
```

### Web Interface

**Access URLs:**

- WiFi AP Mode: `http://192.168.4.1:5000`
- Local Network: `http://<pi-ip>:5000`

**Main Dashboard:**

1. Select Logic (A or B)
2. Select Mode (1-5)
3. Use control buttons:
   - **START**: Begin operation
   - **STOP**: Pause current cycle
   - **EMERGENCY**: Immediate stop
   - **RESET**: Return to home position

**Engineer Menu:**

1. Access: `http://<ip>:5000/engineer`
2. Password: `admin123` (change in config)
3. Edit parameters in real-time
4. View detailed system logs

## Configuration

### System Configuration

Edit `config/system_config.json`:

```json
{
  "web_server": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false
  },
  "logging": {
    "enabled": true,
    "directory": "logs"
  },
  "engineer": {
    "password": "admin123"
  }
}
```

### Logic A Configuration

Edit `config/config_logic_a.json` for speeds, steps, and rotation counts (5 modes).

### Logic B Configuration

Edit `config/config_logic_b.json` for RTC target date and lockout settings.

## Project Structure

```text
RPi_Motor_Control/
├── main.py                     # Application entry point
├── config/
│   ├── config_logic_a.json    # Logic A parameters
│   ├── config_logic_b.json    # Logic B parameters
│   └── system_config.json     # System settings
├── src/
│   ├── hardware_interface.py  # GPIO abstraction
│   ├── motor_controller.py    # Motor/button classes
│   ├── logic_a.py             # Logic A implementation
│   ├── logic_b.py             # Logic B with RTC
│   ├── execution_manager.py   # Logic coordinator
│   ├── web_server.py          # Flask web server
│   ├── rtc_handler.py         # DS3231 interface
│   └── logger.py              # CSV logging
├── templates/
│   └── index.html             # Main dashboard
├── static/
│   ├── css/style.css          # Stylesheets
│   └── js/main.js             # Frontend logic
├── scripts/
│   ├── install.sh             # Quick setup
│   ├── setup_wifi_ap.sh       # WiFi AP config
│   └── motor_control.service  # Systemd service
├── logs/                       # CSV log files
└── requirements.txt            # Python dependencies
```

## Operating Modes

### Logic A (Standard Control)

- 5 operational modes with different speeds/steps
- Manual joystick control
- Automatic homing sequence
- Cycle-based operation

### Logic B (RTC with Date Lockout)

- Extends Logic A functionality
- Monitors DS3231 RTC every second
- Target date: October 13, 2027
- Emergency stop when target date reached
- Different speed profiles than Logic A

## Safety Features

- **Emergency Stop**: Immediate motor shutdown
- **Limit Switch Protection**: Prevents overtravel
- **Date Lockout**: Stops operation on target date (Logic B)
- **Thread-Safe Operations**: Mutex prevents logic conflicts
- **Automatic Logging**: All errors recorded to CSV

## Troubleshooting

### GPIO Errors

```bash
# Check if pigpiod is running
sudo systemctl status pigpiod

# Restart pigpiod
sudo systemctl restart pigpiod
```

### I2C/RTC Issues

```bash
# Check I2C devices
sudo i2cdetect -y 1
# Should show '68' for DS3231

# Enable I2C if needed
sudo raspi-config nonint do_i2c 0
```

### Web Interface Not Loading

```bash
# Check if service is running
sudo systemctl status motor_control

# Check port availability
sudo netstat -tlnp | grep 5000

# View error logs
sudo journalctl -u motor_control -n 50
```

### WiFi AP Not Working

```bash
# Check hostapd status
sudo systemctl status hostapd

# Check dnsmasq status
sudo systemctl status dnsmasq

# Restart WiFi AP
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq
```

### Simulation Issues

- Ensure `--simulate` flag is used
- Check required packages installed

### Motors Not Moving

- Check pigpiod is running: `sudo systemctl status pigpiod`
- Verify wiring and power supply
- Check GPIO permissions

## API Reference

### REST Endpoints

**System Control:**

- `GET /api/status` - Get current system status
- `POST /api/select_logic` - Select Logic A or B
- `POST /api/select_mode` - Select mode 1-5
- `POST /api/start` - Start operation
- `POST /api/stop` - Stop operation
- `POST /api/emergency_stop` - Emergency stop
- `POST /api/reset` - Reset to home

**Configuration:**

- `GET /api/config` - Get current configuration
- `POST /api/config` - Update parameters (engineer only)

**RTC (Logic B):**

- `GET /api/rtc_info` - Get RTC status and date

### WebSocket Events

**Client → Server:**

- `connect` - Establish connection
- `disconnect` - Close connection

**Server → Client:**

- `status_update` - Real-time status broadcast (1Hz)

## License

Proprietary - Omar Project 2025
