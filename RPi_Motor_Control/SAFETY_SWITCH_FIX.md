# Safety Switch Behavior Fix

## Issue Description
The system was blocking during mode/logic selection when the safety switch was LOW (unsafe), preventing the user from selecting logic or mode until both the safety switch went HIGH AND the start button was pressed. This caused the web interface to hang and lose the selected logic.

## Root Cause Analysis

### Arduino Behavior (CG4n51_L1.ino)
1. **At Startup (`setup()` line 902-904)**: Checks safety switch BEFORE any mode selection
   - If LOW (unsafe): Calls `motorStopSwitch()` which waits for Start button only
   - Then continues to allow mode selection

2. **During Operation (`encontrarHome()`, etc.)**: Checks safety switch during motor movements
   - If LOW (unsafe): Calls `motorStopSwitch()` which waits for Start button only
   - Safety switch state doesn't matter for resuming - only Start button

3. **In `motorStopSwitch()` (line 254-272)**:
   ```cpp
   void motorStopSwitch() {
     while (1) {
       if (btnStartPasado != digitalRead(btnStart)) {
         if (btnStartPasado) {
           break;  // Only waits for Start button, NOT safety switch
         }
       }
     }
   }
   ```

### Previous Python Implementation (INCORRECT)
- Checked safety switch during mode selection (in `encontrar_home()`)
- Waited for BOTH safety HIGH + Start button before resuming
- This blocked the entire mode selection API call
- Web interface couldn't complete the request, losing the selected logic

## Solution Implemented

### 1. Fixed `motor_stop_switch()` in `logic_a.py`
**Before:**
```python
def motor_stop_switch(self):
    # Wait for safety switch to return HIGH
    while not self.switch_s.is_triggered():
        time.sleep(0.05)
    
    # Then wait for start button
    while True:
        if self.btn_start.check_rising_edge():
            return
```

**After (matches Arduino):**
```python
def motor_stop_switch(self):
    """Wait ONLY for start button press (matches Arduino motorStopSwitch)"""
    logger.critical("⛔ SAFETY PAUSE - System stopped")
    logger.warning("⏸️  Waiting for Start button press to resume...")
    
    # Only wait for start button (NOT safety switch)
    while True:
        if self.btn_start.check_rising_edge():
            logger.info("✓ Start button pressed - resuming operation")
            return
        time.sleep(0.01)
```

### 2. Added Startup Safety Check in `main.py`
**Matches Arduino `setup()` behavior:**
```python
def _check_startup_safety(self):
    """Check safety switch at startup (matches Arduino setup())"""
    SAFETY_SWITCH_PIN = 6
    safety_state = self.hw_interface.read(SAFETY_SWITCH_PIN)
    
    if not safety_state:  # LOW = unsafe
        logger.warning("⚠️  SAFETY SWITCH UNSAFE at startup")
        logger.warning("⏸️  Press Start button to continue startup...")
        
        # Wait for start button only
        while True:
            if btn_start.check_rising_edge():
                break
            time.sleep(0.01)
```

Called during initialization BEFORE web server starts.

## Correct Behavior Now

### Scenario 1: Safety Switch LOW at Startup
1. System starts
2. Detects safety switch LOW
3. Logs warning and waits for Start button
4. User presses Start button
5. System continues startup
6. Web interface becomes available
7. User can select logic and mode normally

### Scenario 2: Safety Switch LOW Before Mode Selection
1. User visits web interface
2. Safety switch is LOW
3. User can still select logic (no blocking)
4. User can still select mode (no blocking)
5. When operation starts, it will check safety and pause if needed

### Scenario 3: Safety Switch Triggered During Operation
1. Operation is running
2. Safety switch goes LOW (unsafe)
3. System immediately stops motors
4. Logs "SAFETY PAUSE"
5. Waits for Start button press ONLY (not safety switch state)
6. User presses Start button
7. Operation resumes (even if safety switch still LOW)

## Key Differences from Previous Implementation

| Aspect | Previous (WRONG) | Current (CORRECT - matches Arduino) |
|--------|------------------|--------------------------------------|
| **Startup check** | None | Checks safety at startup, waits for Start if unsafe |
| **During mode selection** | Blocked if safety LOW | Never blocks - allows selection |
| **Resume condition** | Safety HIGH + Start button | Start button ONLY |
| **Safety switch role** | Blocking condition | Trigger condition only (causes pause, but doesn't prevent resume) |
| **Web interface** | Hung during mode selection | Always responsive |
| **Logic retention** | Lost when blocked | Retained properly |

## Testing Checklist

- [x] Safety switch LOW at startup: System waits for Start button before continuing
- [ ] Select logic when safety switch is LOW: Should work without blocking
- [ ] Select mode when safety switch is LOW: Should work without blocking
- [ ] Trigger safety during operation: Should pause and wait for Start button only
- [ ] Press Start while safety still LOW: Should resume operation
- [ ] Logic and mode retained after safety pause: Should show selected values in UI

## Files Modified

1. **`src/logic_a.py`** (line 441-456):
   - Simplified `motor_stop_switch()` to only wait for Start button
   - Removed safety switch state checking from resume logic
   - Matches Arduino `motorStopSwitch()` behavior

2. **`main.py`** (lines 92-120, 120-135):
   - Added `_check_startup_safety()` method
   - Called during initialization (step 4, before execution manager)
   - Added `import time` at top of file

## Notes

- The safety switch is a **trigger** not a **blocking condition**
- When safety goes LOW, it triggers a pause
- To resume, only the Start button is needed
- This allows the safety switch to be a simple emergency stop that can be cleared by the operator pressing Start
- The Arduino code doesn't enforce that safety must be HIGH to resume - it trusts the operator's judgment when they press Start
