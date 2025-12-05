#!/bin/bash
# Quick Start Script for RPi Motor Control
# Run this on a fresh Raspberry Pi to set up everything

echo "================================"
echo "RPi Motor Control - Quick Setup"
echo "================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo bash $0"
    exit 1
fi

# Update system
echo "[1/8] Updating system packages..."
apt-get update -y
apt-get upgrade -y

# Install system dependencies
echo "[2/8] Installing system dependencies..."
apt-get install -y python3 python3-pip python3-venv git i2c-tools pigpio python3-pigpio

# Enable I2C and SPI
echo "[3/8] Enabling I2C and SPI interfaces..."
raspi-config nonint do_i2c 0
raspi-config nonint do_spi 0

# Start and enable pigpiod
echo "[4/8] Configuring pigpiod daemon..."
systemctl enable pigpiod
systemctl start pigpiod

# Create virtual environment
echo "[5/8] Creating Python virtual environment..."
cd /home/pi/RPi_Motor_Control
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "[6/8] Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Test RTC (if connected)
echo "[7/8] Testing I2C devices..."
i2cdetect -y 1
echo "If you see '68' above, your DS3231 RTC is connected properly"
sleep 3

# Create systemd service
echo "[8/8] Installing systemd service..."
cp scripts/motor_control.service /etc/systemd/system/
systemctl daemon-reload

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Test the system:"
echo "   cd /home/pi/RPi_Motor_Control"
echo "   source venv/bin/activate"
echo "   python main.py --simulate"
echo ""
echo "2. Enable auto-start on boot:"
echo "   sudo systemctl enable motor_control"
echo "   sudo systemctl start motor_control"
echo ""
echo "3. Check status:"
echo "   sudo systemctl status motor_control"
echo ""
echo "4. View logs:"
echo "   sudo journalctl -u motor_control -f"
echo ""
echo "5. Access web interface:"
echo "   http://$(hostname -I | awk '{print $1}'):5000"
echo ""
