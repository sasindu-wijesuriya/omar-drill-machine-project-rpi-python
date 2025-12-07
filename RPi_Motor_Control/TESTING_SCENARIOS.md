# RPi Motor Control - Complete Testing Scenarios

## Overview

This document provides step-by-step testing procedures for the RPi Motor Control System. Each test scenario can be executed using the GPIO Monitor web interface and API. All actions are logged to journalctl for verification.

## Prerequisites

1. **Service Running**: `sudo systemctl status rpi-motor-control.service` should show active
2. **Web Interface Accessible**: http://localhost:5000
3. **GPIO Monitor Open**: http://localhost:5000/gpio
4. **Log Viewer Open**: Terminal with `sudo journalctl -u rpi-motor-control.service -f`

## Quick Test Commands

```bash
# View real-time logs
sudo journalctl -u rpi-motor-control.service -f

# View logs from last 5 minutes
sudo journalctl -u rpi-motor-control.service --since "5 minutes ago"

# Search for specific events
sudo journalctl -u rpi-motor-control.service | grep "Logic A selected"
```

---

## Test Suite 1: System Initialization

### Test 1.1: Service Startup
**Purpose**: Verify system initializes correctly

**Steps**:
1. Restart service: `sudo systemctl restart rpi-motor-control.service`
2. Check logs: `sudo journalctl -u rpi-motor-control.service -n 50`

**Expected Logs**:
```
✓ Hardware interface initialized
✓ CSV logger initialized
✓ GPIO Monitor initialized
✓ Logic A initialized
✓ Logic B initialized with RTC support
✓ Execution Manager initialized
✓ Web server initialized
✓ System initialization complete
```

**Success Criteria**: All components initialize without errors

---

## Test Suite 2: Logic Selection

### Test 2.1: Select Logic A
**Purpose**: Verify Logic A can be selected

**Steps**:
1. Open web interface: http://localhost:5000
2. Click "Logic A" button in the control panel
3. Verify current logic displays "Logic A - CG4n51_L1"

**API Alternative**:
```bash
curl -X POST http://localhost:5000/api/select_logic \
  -H "Content-Type: application/json" \
  -d '{"logic": "A"}'
```

**Expected Logs**:
```
✓ Logic A selected
✓ Previous logic stopped (if any)
✓ Logic A loaded
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Logic A selected",
  "current_logic": "A"
}
```

**Success Criteria**: 
- Logic A becomes active
- Web interface updates
- No errors in logs

### Test 2.2: Select Logic B
**Purpose**: Verify Logic B can be selected with RTC check

**Steps**:
1. Open web interface: http://localhost:5000
2. Click "Logic B" button in the control panel
3. Verify current logic displays "Logic B - CG4n51_L2"

**API Alternative**:
```bash
curl -X POST http://localhost:5000/api/select_logic \
  -H "Content-Type: application/json" \
  -d '{"logic": "B"}'
```

**Expected Logs**:
```
✓ Logic B selected
✓ Previous logic stopped (if any)
✓ RTC checked
✓ Current date logged
✓ Target date comparison (2027/10/13)
✓ Logic B loaded
```

**Success Criteria**:
- Logic B becomes active
- RTC date is checked and logged
- Date lockout status shown (if applicable)
- No errors in logs

### Test 2.3: Switch Between Logics
**Purpose**: Verify clean switching between logics

**Steps**:
1. Select Logic A
2. Wait 2 seconds
3. Select Logic B
4. Wait 2 seconds
5. Select Logic A again

**Expected Logs** (for each switch):
```
✓ Logic [X] selected
✓ Stopping previous logic [Y]
✓ Logic [Y] stopped
✓ Logic [Y] cleanup complete
✓ Logic [X] loaded
```

**Success Criteria**:
- Clean transitions with no hanging states
- All resources properly released
- No memory leaks or threading issues

---

## Test Suite 3: Mode Selection & Safety Switch

### Test 3.1: Mode Switch Detection
**Purpose**: Verify mode switch (GPIO 6) is detected correctly

**Steps**:
1. Open GPIO Monitor: http://localhost:5000/gpio
2. Set GPIO 6 to HIGH:
   ```bash
   curl -X POST http://localhost:5000/api/gpio/write \
     -H "Content-Type: application/json" \
     -d '{"pin": 6, "value": 1}'
   ```
3. Set GPIO 6 to LOW:
   ```bash
   curl -X POST http://localhost:5000/api/gpio/write \
     -H "Content-Type: application/json" \
     -d '{"pin": 6, "value": 0}'
   ```

**Expected Logs**:
```
✓ GPIO 6 (Mode Switch) set to HIGH
✓ Mode switch state changed: HIGH
✓ GPIO 6 (Mode Switch) set to LOW
✓ Mode switch state changed: LOW
```

**Success Criteria**:
- Mode switch changes are detected
- State is logged
- System responds appropriately

### Test 3.2: Mode 1 Selection (with Logic A)
**Purpose**: Test mode 1 operation

**Prerequisites**: Logic A selected

**Steps**:
1. Set mode switch LOW (Mode 1): GPIO 6 = LOW
2. Press Start button (GPIO 27)
3. Observe system state

**GPIO Commands**:
```bash
# Set Mode 1
curl -X POST http://localhost:5000/api/gpio/write \
  -H "Content-Type: application/json" \
  -d '{"pin": 6, "value": 0}'

# Press Start
curl -X POST http://localhost:5000/api/gpio/button_press \
  -H "Content-Type: application/json" \
  -d '{"pin": 27, "duration": 100}'
```

**Expected Logs**:
```
✓ Mode switch detected: Mode 1 (Automatic)
✓ Start button pressed
✓ Mode 1 parameters loaded
✓ Entering automatic cycle
✓ Cycle phase: INITIAL_DELAY
```

**Success Criteria**:
- Mode 1 activated
- Cycle begins
- Parameters loaded correctly

### Test 3.3: Mode 2 Selection (Manual Mode)
**Purpose**: Test manual mode with joystick

**Prerequisites**: Logic A selected

**Steps**:
1. Set mode switch HIGH (Mode 2): GPIO 6 = HIGH
2. System should enter manual mode

**GPIO Commands**:
```bash
# Set Mode 2 (Manual)
curl -X POST http://localhost:5000/api/gpio/write \
  -H "Content-Type: application/json" \
  -d '{"pin": 6, "value": 1}'
```

**Expected Logs**:
```
✓ Mode switch detected: Mode 2 (Manual)
✓ Entering manual mode
✓ Joystick control enabled
✓ Motor control via joystick active
```

**Success Criteria**:
- Manual mode activated
- Joystick readings logged
- Motors respond to joystick

---

## Test Suite 4: Limit Switches

### Test 4.1: Home Limit Switch
**Purpose**: Verify home limit switch (GPIO 13) detection

**Steps**:
1. Trigger home limit:
   ```bash
   curl -X POST http://localhost:5000/api/gpio/write \
     -H "Content-Type: application/json" \
     -d '{"pin": 13, "value": 0}'
   ```
2. Release home limit:
   ```bash
   curl -X POST http://localhost:5000/api/gpio/write \
     -H "Content-Type: application/json" \
     -d '{"pin": 13, "value": 1}'
   ```

**Expected Logs**:
```
✓ GPIO 13 (Home Limit) set to LOW
✓ Home limit switch TRIGGERED
✓ Motor movement stopped (if moving toward home)
✓ GPIO 13 (Home Limit) set to HIGH
✓ Home limit switch RELEASED
```

**Success Criteria**:
- Home limit triggers properly
- Motion stops when triggered
- State changes logged

### Test 4.2: Final Limit Switch
**Purpose**: Verify final limit switch (GPIO 19) detection

**Steps**:
1. Trigger final limit:
   ```bash
   curl -X POST http://localhost:5000/api/gpio/write \
     -H "Content-Type: application/json" \
     -d '{"pin": 19, "value": 0}'
   ```
2. Release final limit:
   ```bash
   curl -X POST http://localhost:5000/api/gpio/write \
     -H "Content-Type: application/json" \
     -d '{"pin": 19, "value": 1}'
   ```

**Expected Logs**:
```
✓ GPIO 19 (Final Limit) set to LOW
✓ Final limit switch TRIGGERED
✓ Motor movement stopped (if moving toward final)
✓ GPIO 19 (Final Limit) set to HIGH
✓ Final limit switch RELEASED
```

**Success Criteria**:
- Final limit triggers properly
- Motion stops when triggered
- State changes logged

### Test 4.3: Limit Switch During Home Sequence
**Purpose**: Test homing sequence with limit switch

**Prerequisites**: Logic A selected, system idle

**Steps**:
1. Press Reset/Home button (GPIO 17)
2. System should start moving toward home
3. Trigger home limit switch (GPIO 13 = LOW)
4. System should stop at home position

**GPIO Commands**:
```bash
# Start homing
curl -X POST http://localhost:5000/api/gpio/button_press \
  -H "Content-Type: application/json" \
  -d '{"pin": 17, "duration": 100}'

# Wait 2 seconds, then trigger home limit
sleep 2
curl -X POST http://localhost:5000/api/gpio/write \
  -H "Content-Type: application/json" \
  -d '{"pin": 13, "value": 0}'
```

**Expected Logs**:
```
✓ Reset/Home button pressed
✓ Starting home sequence
✓ Moving toward home position
✓ Direction: toward home
✓ Motor LINEAR moving
✓ Home limit switch TRIGGERED
✓ Reached home position
✓ Home sequence complete
✓ Position: Home
```

**Success Criteria**:
- Homing starts
- Motor moves toward home
- Stops at home limit
- Position registered as home

---

## Test Suite 5: Button Controls

### Test 5.1: Reset/Home Button
**Purpose**: Test reset/home functionality

**Steps**:
1. Press Reset/Home button:
   ```bash
   curl -X POST http://localhost:5000/api/gpio/button_press \
     -H "Content-Type: application/json" \
     -d '{"pin": 17, "duration": 100}'
   ```

**Expected Logs**:
```
✓ Button Reset/Home pressed
✓ Reset command received
✓ Stopping current operation (if any)
✓ Starting home sequence
✓ Finding home position
```

**Success Criteria**:
- Reset action triggered
- System returns to home
- All operations stopped

### Test 5.2: Start Button
**Purpose**: Test start functionality

**Prerequisites**: Logic selected, mode selected, system at home

**Steps**:
1. Press Start button:
   ```bash
   curl -X POST http://localhost:5000/api/gpio/button_press \
     -H "Content-Type: application/json" \
     -d '{"pin": 27, "duration": 100}'
   ```

**Expected Logs**:
```
✓ Button Start pressed
✓ Start command received
✓ Mode verified: [Mode 1-5]
✓ Starting automatic cycle
✓ Cycle phase: INITIAL_DELAY
✓ Loading cycle parameters
```

**Success Criteria**:
- Cycle starts
- Parameters loaded
- Motors begin movement

### Test 5.3: Stop Button
**Purpose**: Test emergency stop

**Prerequisites**: System running

**Steps**:
1. Start a cycle (press Start button)
2. Wait 2 seconds
3. Press Stop button:
   ```bash
   curl -X POST http://localhost:5000/api/gpio/button_press \
     -H "Content-Type: application/json" \
     -d '{"pin": 22, "duration": 100}'
   ```

**Expected Logs**:
```
✓ Button Stop pressed
✓ EMERGENCY STOP triggered
✓ Stopping all motors
✓ Motor LINEAR stopped
✓ Motor DRILL stopped
✓ Cycle interrupted
✓ System state: STOPPED
```

**Success Criteria**:
- Immediate stop
- All motors halt
- Safe state achieved
- Can resume operation

### Test 5.4: Tala/Drill Button
**Purpose**: Test drill button functionality

**Steps**:
1. Press Tala/Drill button:
   ```bash
   curl -X POST http://localhost:5000/api/gpio/button_press \
     -H "Content-Type: application/json" \
     -d '{"pin": 5, "duration": 100}'
   ```

**Expected Logs**:
```
✓ Button Tala/Drill pressed
✓ Drill command received
✓ Drill motor activation requested
```

**Success Criteria**:
- Drill command registered
- Appropriate action taken based on logic

---

## Test Suite 6: Motor Parameters

### Test 6.1: View Current Parameters
**Purpose**: Verify parameter configuration

**Steps**:
1. Open Engineer Menu: http://localhost:5000/engineer
2. Login with password: 1234
3. View Logic A parameters
4. View Logic B parameters

**API Alternative**:
```bash
# Login
curl -X POST http://localhost:5000/api/engineer/login \
  -H "Content-Type: application/json" \
  -d '{"password": "1234"}' \
  -c cookies.txt

# Get Logic A config
curl -X GET http://localhost:5000/api/config/A \
  -b cookies.txt

# Get Logic B config
curl -X GET http://localhost:5000/api/config/B \
  -b cookies.txt
```

**Expected Logs**:
```
✓ Engineer login successful
✓ Configuration requested for Logic A
✓ Configuration data retrieved
```

**Success Criteria**:
- Can access engineer menu
- Parameters displayed correctly
- Values match config files

### Test 6.2: Update Parameter
**Purpose**: Test parameter modification

**Prerequisites**: Engineer menu logged in

**Steps**:
1. Update a parameter (e.g., velocidad_lineal_home):
   ```bash
   curl -X POST http://localhost:5000/api/config/update \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "logic": "A",
       "parameter": "velocidades_lineal.home",
       "value": 4500
     }'
   ```

**Expected Logs**:
```
✓ Parameter update requested
✓ Logic: A
✓ Parameter: velocidades_lineal.home
✓ Old value: 4000
✓ New value: 4500
✓ Parameter updated successfully
✓ Configuration saved
```

**Success Criteria**:
- Parameter updates
- Old/new values logged
- Change persisted
- System uses new value

### Test 6.3: Verify Parameters in Operation
**Purpose**: Confirm updated parameters are used

**Steps**:
1. Update a speed parameter
2. Start a cycle
3. Observe motor speed in logs

**Expected Logs**:
```
✓ Using velocity: 4500 (updated value)
✓ Motor speed set to 4500
```

**Success Criteria**:
- New parameter value used
- Operation reflects change

---

## Test Suite 7: Complete Cycle Tests

### Test 7.1: Full Automatic Cycle (Logic A, Mode 1)
**Purpose**: Execute complete automatic cycle

**Prerequisites**: 
- Logic A selected
- System at home position
- Mode 1 selected

**Steps**:
1. Set mode switch to Mode 1 (GPIO 6 = LOW)
2. Press Start button
3. Let cycle complete
4. Monitor logs throughout

**Expected Log Sequence**:
```
✓ Mode 1 selected
✓ Start button pressed
✓ Starting automatic cycle
✓ Cycle phase: INITIAL_DELAY
✓ Delay complete
✓ Cycle phase: CYCLE_1
✓ Moving to position 1
✓ Steps: [X], Velocity: [Y]
✓ Motor LINEAR moving
✓ Drill operation: [action]
✓ Motor DRILL moving
✓ Cycle 1 complete
✓ Cycle phase: INTERMEDIATE
✓ Moving to intermediate position
✓ Intermediate movement complete
✓ Cycle phase: CYCLE_2
✓ Moving to position 2
✓ Cycle 2 complete
✓ Cycle phase: COMPLETE
✓ Returning to home
✓ Home limit reached
✓ Cycle finished successfully
```

**Success Criteria**:
- Complete cycle execution
- All phases logged
- Motors move correctly
- Returns to home
- No errors

### Test 7.2: Cycle with Stop and Resume
**Purpose**: Test stop and resume functionality

**Steps**:
1. Start cycle
2. Wait until CYCLE_1 phase
3. Press Stop button
4. Wait 2 seconds
5. Press Start button again

**Expected Logs**:
```
✓ Cycle started
✓ Cycle phase: CYCLE_1
✓ Stop button pressed
✓ EMERGENCY STOP
✓ Cycle paused at phase: CYCLE_1
✓ Position saved: [X]
✓ Start button pressed
✓ Resuming from saved position
✓ Continuing cycle from CYCLE_1
```

**Success Criteria**:
- Cycle stops cleanly
- Position preserved
- Can resume from stop point

---

## Test Suite 8: Logic B Specific Tests

### Test 8.1: RTC Date Check
**Purpose**: Verify RTC is being checked

**Prerequisites**: Logic B selected

**Steps**:
1. Select Logic B
2. Check logs for RTC information

**Expected Logs**:
```
✓ Logic B selected
✓ RTC initialized
✓ Current date: 2025-12-06
✓ Target date: 2027-10-13
✓ Days until target: [X]
✓ Date lockout: NOT ACTIVE
```

**Success Criteria**:
- RTC date retrieved
- Target date compared
- Lockout status clear

### Test 8.2: Date Lockout Test (Simulated)
**Purpose**: Test what happens if target date reached

**Note**: This requires modifying target date in config temporarily

**Steps**:
1. Edit `/home/ubuntu/omar-drill-machine-project-rpi-python/RPi_Motor_Control/config/config_logic_b.json`
2. Set target date to past date (e.g., 2020-01-01)
3. Restart service
4. Select Logic B

**Expected Logs**:
```
✓ Logic B initializing
✓ RTC initialized
✓ Current date: 2025-12-06
✓ Target date: 2020-01-01
✓ ⚠️ TARGET DATE HAS BEEN REACHED!
✓ Date lockout: ACTIVE
✓ ⚠️ System will not operate
```

**Success Criteria**:
- Lockout detected
- Clear warnings in logs
- System refuses to operate

---

## Test Suite 9: Error Conditions

### Test 9.1: Invalid Logic Selection
**Purpose**: Test error handling

**Steps**:
```bash
curl -X POST http://localhost:5000/api/select_logic \
  -H "Content-Type: application/json" \
  -d '{"logic": "C"}'
```

**Expected Response**:
```json
{
  "error": "Invalid logic. Must be 'A' or 'B'"
}
```

**Expected Logs**:
```
✓ Invalid logic selection attempt: C
✓ Error: Invalid logic specified
```

### Test 9.2: Start Without Mode Selection
**Purpose**: Test safety checks

**Steps**:
1. Select Logic A
2. Press Start without selecting mode

**Expected Logs**:
```
✓ Start button pressed
✓ ⚠️ Cannot start: No mode selected
✓ Error: Mode must be selected first
```

### Test 9.3: GPIO Write to Protected Pin
**Purpose**: Test GPIO safety

**Steps**:
```bash
# Try to write to motor output pin
curl -X POST http://localhost:5000/api/gpio/write \
  -H "Content-Type: application/json" \
  -d '{"pin": 18, "value": 1}'
```

**Expected Response**:
```json
{
  "success": false,
  "message": "Pin 18 (Linear STEP) cannot be written to..."
}
```

**Expected Logs**:
```
✓ GPIO write attempt to protected pin 18
✓ Write blocked: Pin is motor output
```

---

## Test Suite 10: Web Interface Tests

### Test 10.1: Real-time Status Updates
**Purpose**: Verify WebSocket updates

**Steps**:
1. Open main dashboard
2. Start a cycle
3. Observe real-time status updates

**Expected Behavior**:
- Status updates every 100-500ms
- Current position shown
- Cycle phase displayed
- Motor states updated

### Test 10.2: GPIO Monitor Auto-Refresh
**Purpose**: Test GPIO monitor updates

**Steps**:
1. Open GPIO Monitor
2. Enable Auto-Refresh
3. Change pin states via API
4. Observe updates

**Expected Behavior**:
- Pins update automatically
- Changes reflected within 500ms
- No lag or missing updates

---

## Complete Test Script

Here's a bash script to run through basic tests:

```bash
#!/bin/bash

API="http://localhost:5000"

echo "==== RPi Motor Control Test Suite ===="
echo ""

echo "Test 1: Select Logic A"
curl -X POST $API/api/select_logic -H "Content-Type: application/json" -d '{"logic": "A"}'
echo ""
sleep 2

echo "Test 2: Select Logic B"
curl -X POST $API/api/select_logic -H "Content-Type: application/json" -d '{"logic": "B"}'
echo ""
sleep 2

echo "Test 3: Set Mode Switch LOW"
curl -X POST $API/api/gpio/write -H "Content-Type: application/json" -d '{"pin": 6, "value": 0}'
echo ""
sleep 1

echo "Test 4: Press Start Button"
curl -X POST $API/api/gpio/button_press -H "Content-Type: application/json" -d '{"pin": 27, "duration": 100}'
echo ""
sleep 3

echo "Test 5: Press Stop Button"
curl -X POST $API/api/gpio/button_press -H "Content-Type: application/json" -d '{"pin": 22, "duration": 100}'
echo ""
sleep 1

echo "Test 6: Trigger Home Limit"
curl -X POST $API/api/gpio/write -H "Content-Type: application/json" -d '{"pin": 13, "value": 0}'
echo ""
sleep 1

echo "Test 7: Release Home Limit"
curl -X POST $API/api/gpio/write -H "Content-Type: application/json" -d '{"pin": 13, "value": 1}'
echo ""

echo "==== Tests Complete ===="
echo "Check logs with: sudo journalctl -u rpi-motor-control.service -n 100"
```

Save as `test_scenarios.sh` and run with `bash test_scenarios.sh`

---

## Log Viewing Tips

### Real-time Monitoring
```bash
# Follow logs in real-time
sudo journalctl -u rpi-motor-control.service -f

# With timestamp
sudo journalctl -u rpi-motor-control.service -f --output=short-iso

# Filter by priority
sudo journalctl -u rpi-motor-control.service -f -p info
```

### Searching Logs
```bash
# Search for logic selection
sudo journalctl -u rpi-motor-control.service | grep "Logic.*selected"

# Search for button presses
sudo journalctl -u rpi-motor-control.service | grep "Button.*pressed"

# Search for errors
sudo journalctl -u rpi-motor-control.service -p err

# Search for motor movements
sudo journalctl -u rpi-motor-control.service | grep "Motor.*moving"
```

### Export Logs
```bash
# Save last hour to file
sudo journalctl -u rpi-motor-control.service --since "1 hour ago" > test_logs.txt

# Save specific test run
sudo journalctl -u rpi-motor-control.service --since "2025-12-06 16:00:00" --until "2025-12-06 17:00:00" > test_run_1.txt
```

---

## Success Criteria Summary

A complete test is successful when:

✅ All expected logs appear in journalctl  
✅ No ERROR or CRITICAL logs (except intentional error tests)  
✅ System state changes as expected  
✅ GPIO pins respond correctly  
✅ Motors move (in simulation, this is logged)  
✅ Cycles complete without hanging  
✅ Web interface updates in real-time  
✅ Parameters can be modified  
✅ Emergency stop works immediately  
✅ System recovers from errors gracefully  

---

## Next Steps After Testing

1. Document any failures or unexpected behavior
2. Save test logs for review
3. Create issues for any bugs found
4. Update parameters based on testing
5. Prepare for hardware testing on actual Raspberry Pi
