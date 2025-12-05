#!/bin/bash
# Setup WiFi Access Point on Raspberry Pi
# This creates a standalone WiFi hotspot for accessing the motor control system

echo "================================="
echo "WiFi Access Point Setup"
echo "================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo bash $0"
    exit 1
fi

# Install required packages
echo "[1/5] Installing hostapd and dnsmasq..."
apt-get update
apt-get install -y hostapd dnsmasq

# Stop services
systemctl stop hostapd
systemctl stop dnsmasq

# Configure static IP for wlan0
echo "[2/5] Configuring static IP..."
cat >> /etc/dhcpcd.conf << EOF

# Static IP for WiFi AP
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
EOF

# Configure dnsmasq
echo "[3/5] Configuring DHCP server..."
mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
cat > /etc/dnsmasq.conf << EOF
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
domain=wlan
address=/rpimotor.local/192.168.4.1
EOF

# Configure hostapd
echo "[4/5] Configuring WiFi access point..."
cat > /etc/hostapd/hostapd.conf << EOF
interface=wlan0
driver=nl80211
ssid=RPi_MotorControl
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=motorcontrol123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Point hostapd to config file
echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' >> /etc/default/hostapd

# Enable IP forwarding (optional, for internet sharing)
echo "[5/5] Enabling IP forwarding..."
sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf

# Enable services
systemctl unmask hostapd
systemctl enable hostapd
systemctl enable dnsmasq

echo ""
echo "================================="
echo "WiFi AP Setup Complete!"
echo "================================="
echo ""
echo "WiFi Network Details:"
echo "  SSID:     RPi_MotorControl"
echo "  Password: motorcontrol123"
echo "  IP:       192.168.4.1"
echo ""
echo "Web Interface:"
echo "  URL: http://192.168.4.1:5000"
echo ""
echo "⚠️  IMPORTANT: Reboot required!"
echo "Run: sudo reboot"
echo ""
echo "After reboot:"
echo "1. Connect to WiFi: RPi_MotorControl"
echo "2. Open browser: http://192.168.4.1:5000"
echo ""
