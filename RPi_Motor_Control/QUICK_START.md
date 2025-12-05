# Quick Start Guide

## For Development/Testing (No Hardware)

```bash
# Install dependencies
pip install -r requirements.txt

# Run simulation mode
python main.py --simulate

# Open browser
http://localhost:5000
```

## For Raspberry Pi Deployment

### One-Line Install

```bash
sudo bash scripts/install.sh
```

### WiFi Hotspot Setup

```bash
sudo bash scripts/setup_wifi_ap.sh
sudo reboot
```

After reboot:

- **WiFi SSID**: `RPi_MotorControl`
- **Password**: `motorcontrol123`
- **Web Interface**: `http://192.168.4.1:5000`

## Basic Operation

### 1. Select Logic

- **Logic A**: Standard motor control (5 modes)
- **Logic B**: RTC-based with date lockout

### 2. Select Mode

Choose mode 1-5 (each has different speeds/steps)

### 3. Control

- **START**: Begin operation
- **STOP**: Pause cycle
- **EMERGENCY**: Immediate stop
- **RESET**: Return to home position

## Engineer Access

- **URL**: `http://<ip>:5000/engineer`
- **Password**: `admin123` (change in `config/system_config.json`)

## Troubleshooting

### Service not starting?

```bash
sudo systemctl status motor_control
sudo journalctl -u motor_control -f
```

### GPIO not working?

```bash
sudo systemctl restart pigpiod
```

### RTC not detected?

```bash
sudo i2cdetect -y 1  # Should show '68'
```

## Configuration Files

- `config/config_logic_a.json` - Logic A parameters
- `config/config_logic_b.json` - Logic B parameters
- `config/system_config.json` - System settings

## Logs

Located in `logs/` directory:

- `operations.csv` - Operation history
- `parameters.csv` - Parameter changes
- `errors.csv` - Error log

## Command Line Options

```bash
python main.py --simulate      # Simulation mode
python main.py --debug         # Debug logging
python main.py --port 8080     # Custom port
```

## GPIO Pinout Quick Reference

| Motor   | STEP    | DIR     |
| ------- | ------- | ------- |
| Motor 1 | GPIO 18 | GPIO 23 |
| Motor 2 | GPIO 24 | GPIO 25 |

| Button | GPIO |
| ------ | ---- |
| Reset  | 17   |
| Start  | 27   |
| Stop   | 22   |
| Tala   | 5    |

| Limit Switch | GPIO |
| ------------ | ---- |
| Home         | 13   |
| Final        | 19   |
| Mode Switch  | 6    |

## Support

For detailed documentation, see `README.md`
