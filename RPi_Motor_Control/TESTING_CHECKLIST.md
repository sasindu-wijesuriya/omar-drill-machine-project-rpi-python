# Testing Checklist

## Pre-Deployment Testing (Simulation Mode)

### ✅ System Initialization

- [x] Load configuration files
- [x] Initialize hardware interface (simulated)
- [x] Create CSV logger
- [x] Initialize Logic A
- [x] Initialize Logic B
- [x] Create execution manager
- [x] Start web server
- [x] WebSocket connection established

### ✅ Web Interface

- [x] Access main dashboard (http://localhost:5000)
- [x] Logic A/B selector visible
- [x] Mode selector (1-5) visible
- [x] Control buttons displayed
- [x] Status panel shows data
- [ ] Engineer login page
- [ ] Engineer menu (parameter editing)
- [ ] Logs viewing page

### ⏳ Logic A Testing (Simulation)

- [ ] Select Logic A
- [ ] Select Mode 1
- [ ] Click START
- [ ] Verify status updates
- [ ] Click STOP
- [ ] Click EMERGENCY
- [ ] Click RESET
- [ ] Test Mode 2-5
- [ ] Check CSV logs created

### ⏳ Logic B Testing (Simulation)

- [ ] Select Logic B
- [ ] Verify RTC status shows (simulated)
- [ ] Check days until target date
- [ ] Select Mode 1
- [ ] Click START
- [ ] Verify RTC checking every second
- [ ] Test all modes
- [ ] Check CSV logs

### ⏳ API Testing

- [ ] GET /api/status
- [ ] POST /api/select_logic (A)
- [ ] POST /api/select_logic (B)
- [ ] POST /api/select_mode (1-5)
- [ ] POST /api/start
- [ ] POST /api/stop
- [ ] POST /api/emergency_stop
- [ ] POST /api/reset
- [ ] GET /api/rtc_info (Logic B)

---

## Hardware Deployment Testing (Raspberry Pi)

### 🔧 Installation

- [ ] Run `sudo bash scripts/install.sh`
- [ ] Verify all dependencies installed
- [ ] Check pigpiod service running
- [ ] Verify I2C enabled
- [ ] Verify SPI enabled
- [ ] Check virtual environment created

### 🔌 Hardware Connections

- [ ] Motor 1 STEP → GPIO 18
- [ ] Motor 1 DIR → GPIO 23
- [ ] Motor 2 STEP → GPIO 24
- [ ] Motor 2 DIR → GPIO 25
- [ ] Reset button → GPIO 17
- [ ] Start button → GPIO 27
- [ ] Stop button → GPIO 22
- [ ] Tala button → GPIO 5
- [ ] Home limit → GPIO 13
- [ ] Final limit → GPIO 19
- [ ] Mode switch → GPIO 6
- [ ] DS3231 SDA → GPIO 2
- [ ] DS3231 SCL → GPIO 3
- [ ] MCP3008 connected (SPI)

### 🔍 Hardware Verification

- [ ] Run `sudo i2cdetect -y 1` (should show 0x68)
- [ ] Check motor driver power supply
- [ ] Test limit switches continuity
- [ ] Test buttons with multimeter
- [ ] Verify joystick analog output

### 🌐 WiFi AP Setup

- [ ] Run `sudo bash scripts/setup_wifi_ap.sh`
- [ ] Reboot Pi
- [ ] Find WiFi network: `RPi_MotorControl`
- [ ] Connect with password: `motorcontrol123`
- [ ] Access http://192.168.4.1:5000
- [ ] Verify web interface loads

### 🏃 Operation Testing

- [ ] Start service: `sudo systemctl start motor_control`
- [ ] Check status: `sudo systemctl status motor_control`
- [ ] Access web interface
- [ ] Select Logic A
- [ ] Select Mode 1
- [ ] Click RESET (motors should home)
- [ ] Click START (cycle should run)
- [ ] Click STOP (should pause)
- [ ] Click START (should resume)
- [ ] Click EMERGENCY (should stop immediately)
- [ ] Test manual joystick control

### 📊 Logic A Hardware Tests

- [ ] Mode 1: Full cycle
- [ ] Mode 2: Full cycle
- [ ] Mode 3: Full cycle
- [ ] Mode 4: Full cycle
- [ ] Mode 5: Full cycle
- [ ] Home finding on startup
- [ ] Limit switch detection
- [ ] Button debouncing
- [ ] Joystick manual control
- [ ] Check CSV logs

### 📊 Logic B Hardware Tests

- [ ] Check RTC time accuracy
- [ ] Verify RTC date display
- [ ] Check "days until target" countdown
- [ ] Run Mode 1 cycle
- [ ] Verify RTC monitoring (every 1sec)
- [ ] Test all 5 modes
- [ ] Simulate target date approach
- [ ] Check CSV logs

### 🔒 Safety Tests

- [ ] Emergency stop response time
- [ ] Limit switch override
- [ ] Home limit detection
- [ ] Final limit detection
- [ ] Mode switch behavior
- [ ] Power loss recovery
- [ ] Concurrent logic prevention (mutex)

### 📝 Logging Tests

- [ ] Check `logs/operations.csv` exists
- [ ] Verify timestamps correct
- [ ] Check `logs/parameters.csv` logs config changes
- [ ] Check `logs/errors.csv` logs errors
- [ ] Verify log rotation (if implemented)

### 🔄 Auto-Start Tests

- [ ] Enable service: `sudo systemctl enable motor_control`
- [ ] Reboot Pi
- [ ] Verify service starts automatically
- [ ] Check web interface accessible
- [ ] Test normal operation after auto-start

---

## Performance Testing

### ⏱ Timing Accuracy

- [ ] Measure step pulse width (oscilloscope)
- [ ] Verify speed matches config
- [ ] Check acceleration/deceleration
- [ ] Test microsecond delays

### 📈 Resource Monitoring

- [ ] Check CPU usage: `top`
- [ ] Check RAM usage: `free -h`
- [ ] Monitor temperature: `vcgencmd measure_temp`
- [ ] Check network traffic during operation

### 🔄 Stress Testing

- [ ] Run 100 consecutive cycles
- [ ] Switch logics 50 times
- [ ] Rapid START/STOP cycles
- [ ] Multiple emergency stops
- [ ] Long-duration operation (8 hours)

---

## Edge Cases & Error Handling

### 🐛 Error Scenarios

- [ ] Start without homing
- [ ] Trigger limit switch during operation
- [ ] Press STOP during homing
- [ ] Emergency stop during cycle
- [ ] Disconnect RTC during operation (Logic B)
- [ ] Invalid mode selection
- [ ] Invalid logic selection
- [ ] Network disconnection (web interface)
- [ ] Power brownout simulation

### 🔧 Recovery Testing

- [ ] Restart after crash
- [ ] Resume after emergency stop
- [ ] Reconnect after WiFi loss
- [ ] Recover from GPIO errors
- [ ] Handle I2C communication failures

---

## Web Interface Testing

### 🖥 Browser Compatibility

- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari
- [ ] Mobile browser (responsive)

### 📱 Mobile Testing

- [ ] Portrait orientation
- [ ] Landscape orientation
- [ ] Touch controls
- [ ] Status updates on mobile

### 🔌 WebSocket Testing

- [ ] Real-time status updates
- [ ] Auto-reconnect on disconnect
- [ ] Multiple clients simultaneously
- [ ] Status update frequency (1Hz)

---

## Documentation Verification

### 📚 Documentation Completeness

- [x] README.md complete
- [x] QUICK_START.md created
- [x] IMPLEMENTATION_SUMMARY.md created
- [ ] Code comments reviewed
- [ ] API documentation accurate
- [ ] Pin mapping verified
- [ ] Configuration examples valid

---

## Security Testing

### 🔐 Access Control

- [ ] Engineer menu password protection
- [ ] Session management
- [ ] CORS configuration
- [ ] Input validation
- [ ] SQL injection prevention (if database added)

---

## Final Checklist

### 🎯 Pre-Production

- [ ] All critical tests passed
- [ ] Documentation reviewed
- [ ] Installation scripts tested
- [ ] WiFi AP working
- [ ] Auto-start configured
- [ ] Logs verified
- [ ] Safety features tested
- [ ] Performance acceptable

### 📦 Production Deployment

- [ ] Backup current system
- [ ] Deploy to production Pi
- [ ] Verify all connections
- [ ] Test full operation cycle
- [ ] Train operators
- [ ] Document known issues
- [ ] Create maintenance schedule

---

## Notes Section

### Test Results

```
Date: _____________
Tester: ___________

Critical Issues:
-

Minor Issues:
-

Observations:
-

Recommendations:
-
```

### Hardware Issues Log

```
Issue:
Date:
Resolution:

Issue:
Date:
Resolution:
```

---

## Sign-Off

**Testing Completed By**: ********\_\_\_********  
**Date**: ********\_\_\_********  
**Approved By**: ********\_\_\_********  
**Date**: ********\_\_\_********

**Status**:

- [ ] Approved for Production
- [ ] Requires Fixes
- [ ] Failed Testing

**Comments**:

---

---

---
