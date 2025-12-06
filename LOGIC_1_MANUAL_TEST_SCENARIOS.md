# Logic 1 (CG4n51_L1) - Complete Manual Testing Guide

## 📋 Overview

This document provides step-by-step testing scenarios for **Logic 1** of the drill machine controller. Logic 1 is the standard control logic without RTC (Real-Time Clock) checking.

---

## 🎯 Test Coverage

- ✅ Manual Mode with Joystick
- ✅ Automatic Mode - All 5 Operating Modes
- ✅ Safety Features (Stop, Reset, Safety Switch)
- ✅ Home Finding and Positioning
- ✅ Limit Switch Protection
- ✅ Emergency Stop Scenarios

---

## 🔧 Prerequisites

### Hardware Setup

- [ ] GPIO Simulator running on port 8100
- [ ] Motor Control app running on port 5000
- [ ] Safety switch (GPIO 6) is ON (HIGH)
- [ ] All limit switches (GPIO 13, 19) are released (HIGH)
- [ ] All buttons (GPIO 5, 17, 22, 27) are released (HIGH)

### Access Points

- **GPIO Simulator UI**: http://localhost:8100 (or your PC's IP:8100)
- **Motor Control UI**: http://localhost:5000 (or your PC's IP:5000)

---

## 📖 Test Scenarios

---

## **SCENARIO 1: System Startup and Initialization**

### Story

_"The machine is powered on for the first time today. The operator needs to ensure the system initializes correctly and finds its home position."_

### Steps

#### 1.1 Power-On Check

1. **Start both applications** (Simulator and Motor Control)
2. **Open both UIs** in separate browser tabs
3. **Verify in Simulator UI**:
   - All buttons show "Released" state
   - All limit switches are OFF (not triggered)
   - Motor outputs are all LOW (0)
   - Safety switch is ON

**Expected Result**:

- ✅ System initializes
- ✅ No errors displayed
- ✅ Ready for commands

#### 1.2 First Home Sequence

1. **In Motor Control UI**: Select **"Logic A"** from dropdown
2. **Click** "Select Mode 1" button
3. **Watch Simulator UI**:
   - Motor 1 Direction (GPIO 23) should change
   - Motor 1 Pulsos (GPIO 18) should start pulsing

**Expected Result**:

- ✅ Linear motor moves toward home
- ✅ GPIO 23 (dir1) = 1 (toward home direction)
- ✅ GPIO 18 (pulsos1) toggles rapidly
- ✅ Activity log shows motor movement

#### 1.3 Home Detection

1. **In Simulator UI**: Toggle **"Home Limit (GPIO 13)"** switch to ON
2. **Observe**: Motor should stop immediately
3. **Wait**: Motor reverses slightly to position after home

**Expected Result**:

- ✅ Motor stops when home switch triggered
- ✅ Motor reverses for ~425 steps
- ✅ Final position is established
- ✅ System displays "CARGAR PIEZAS" (Load pieces)
- ✅ System displays "PRESIONE ARRANCAR" (Press Start)

---

## **SCENARIO 2: Manual Mode Operation**

### Story

_"An operator needs to manually position the drill head for maintenance. They use the joystick to control linear movement and the Tala button to control the drill motor."_

### Steps

#### 2.1 Enter Manual Mode

1. **Ensure**: System is at home (not in automatic cycle)
2. **In Motor Control UI**: Click **"Enable Manual Mode"** button
3. **Verify**: UI shows "Manual Mode Active"

**Expected Result**:

- ✅ Manual mode indicator shows
- ✅ Joystick becomes active
- ✅ System ready for manual control

#### 2.2 Test Joystick - Move Toward Final

1. **In Simulator UI**: Observe GPIO values
2. **In Motor Control UI**: Use joystick slider or simulate joystick > 652
3. **Move slider RIGHT** (toward final position)

**Expected Result**:

- ✅ GPIO 23 (dir1) = 0 (toward final direction)
- ✅ GPIO 18 (pulsos1) pulses at rate based on joystick position
- ✅ Speed increases as you move joystick further right
- ✅ Activity log shows linear movement

#### 2.3 Test Joystick - Move Toward Home

1. **Move slider LEFT** (toward home position)
2. **Watch GPIOs** change

**Expected Result**:

- ✅ GPIO 23 (dir1) = 1 (toward home direction)
- ✅ GPIO 18 (pulsos1) pulses at rate based on joystick position
- ✅ Speed increases as you move joystick further left

#### 2.4 Test Joystick - Center (Stop)

1. **Center the joystick** slider (value between 352-652)

**Expected Result**:

- ✅ GPIO 18 (pulsos1) stops pulsing
- ✅ Motor 1 outputs go to 0
- ✅ Linear motor stops

#### 2.5 Test Drill Motor (Tala Button)

1. **In Simulator UI**: Click and hold **"Tala (GPIO 5)"** button
2. **Hold for 1 second**, then release

**Expected Result**:

- ✅ GPIO 24 (pulsos2) starts pulsing when button pressed
- ✅ Motor 2 LED indicators light up
- ✅ Drill motor toggles ON when button pressed

3. **Press Tala button again**

**Expected Result**:

- ✅ GPIO 24 (pulsos2) stops pulsing
- ✅ Drill motor toggles OFF

#### 2.6 Test Home Limit Protection in Manual Mode

1. **Move joystick LEFT** (toward home)
2. **While moving**: Toggle **"Home Limit (GPIO 13)"** ON in simulator

**Expected Result**:

- ✅ Motor stops immediately
- ✅ Motor automatically reverses ~300 steps
- ✅ Motor stops again
- ✅ Activity log shows "Sensor home activated, rebotando"

#### 2.7 Test Final Limit Protection in Manual Mode

1. **Move joystick RIGHT** (toward final)
2. **While moving**: Toggle **"Final Limit (GPIO 19)"** ON in simulator

**Expected Result**:

- ✅ Motor stops immediately
- ✅ Motor automatically reverses ~300 steps
- ✅ Motor stops again
- ✅ Activity log shows "Sensor final activated, rebotando"

#### 2.8 Exit Manual Mode

1. **In Motor Control UI**: Click **"Disable Manual Mode"**

**Expected Result**:

- ✅ Manual mode indicator disappears
- ✅ Joystick becomes inactive
- ✅ All motor outputs stop

---

## **SCENARIO 3: Automatic Mode - Mode 1 (Full Cycle)**

### Story

_"An operator loads a workpiece for Mode 1 processing. This mode performs 100 rotations in level 1 and 1000 rotations in level 2."_

### Steps

#### 3.1 Select Mode 1

1. **Ensure**: System is at home position
2. **In Motor Control UI**: Click **"Select Mode 1"**
3. **Wait**: System performs home sequence

**Expected Result**:

- ✅ System goes to home
- ✅ Display shows "MODO 1 SELECCIONADO"
- ✅ Display shows "CARGAR PIEZAS"
- ✅ Display shows "PRESIONE ARRANCAR"

#### 3.2 Load Workpiece

_In real operation, operator would load material here_

1. **Verify**: Safety switch (GPIO 6) is ON
2. **Verify**: System is waiting for start

**Expected Result**:

- ✅ System in waiting state
- ✅ No motor movement
- ✅ Ready for start command

#### 3.3 Start Cycle

1. **In Simulator UI**: Click and hold **"Start (GPIO 27)"** button
2. **Hold for 1 second**, then release

**Expected Result**:

- ✅ Display changes to execution page (page 3)
- ✅ Drill motor (GPIO 24) starts spinning immediately
- ✅ 2-second delay before linear movement begins
- ✅ Activity log shows "Drill motor starting"

#### 3.4 Watch Cycle 1 (Level 1) Execution

1. **Observe GPIOs**:

   - GPIO 23 (dir1) alternates (0 and 1)
   - GPIO 18 (pulsos1) pulses continuously
   - GPIO 24 (pulsos2) pulses continuously

2. **Watch display**: Rotation counter increments

**Expected Result**:

- ✅ Linear motor moves forward 175 steps (Mode 1 level 1 distance)
- ✅ Linear motor reverses back 175 steps
- ✅ Drill motor spins throughout
- ✅ This repeats 100 times (cantidadPrimerNivel1 = 100)
- ✅ Counter shows rotation progress
- ✅ Speed matches velocidadLineal1 (3000) and velocidadTaladro1 (2200)

#### 3.5 Watch Intermediate Movement

1. **After 100 rotations complete**:
   - System pauses briefly (1 second)
   - Linear motor moves 175 steps forward (pasosAcomodoParaSegundoNivel1)

**Expected Result**:

- ✅ Linear motor advances to level 2 position
- ✅ No backward movement during this phase
- ✅ Drill motor stops during positioning

#### 3.6 Watch Cycle 2 (Level 2) Execution

1. **Observe new pattern**:
   - Linear moves forward 225 steps (cantidadPasosSegundoNivel2)
   - Linear moves backward 225 steps
   - After EACH backward movement, drill makes additional 200 steps
   - This happens for 3 rotations (cantidadGirosTaladroCiclo2)

**Expected Result**:

- ✅ Linear motor moves in level 2 pattern
- ✅ Additional drill pulses after each cycle
- ✅ Pattern repeats 3 times
- ✅ Display updates counter

#### 3.7 Cycle Complete

1. **After all rotations**:
   - System stops
   - Display shows completion message

**Expected Result**:

- ✅ All motors stop
- ✅ Display shows "ABRIR Y DESCARGUE" (Open and unload)
- ✅ Display shows "PRESIONE INICIO PARA SIG. CICLO" (Press start for next cycle)
- ✅ All GPIO outputs return to 0

#### 3.8 Reset to Home

1. **In Simulator UI**: Click and hold **"Reset (GPIO 17)"** button
2. **Hold briefly**, then release

**Expected Result**:

- ✅ System returns to home position
- ✅ Display returns to mode selection page (page 1)
- ✅ All counters reset to 0
- ✅ System ready for next cycle

---

## **SCENARIO 4: Automatic Mode - Mode 2**

### Story

_"Mode 2 processing requires different speeds and rotation counts than Mode 1."_

### Configuration Differences (Mode 2)

- Level 1: 400 rotations (vs 100 in Mode 1)
- Level 2: 800 rotations (vs 1000 in Mode 1)
- Linear speed: 7000 (vs 3000 in Mode 1)
- Steps level 1: 380 (vs 175 in Mode 1)
- Steps level 2: 80 (vs 225 in Mode 1)

### Steps

#### 4.1 Select Mode 2

1. **In Motor Control UI**: Click **"Select Mode 2"**
2. **Wait**: System goes to home

**Expected Result**:

- ✅ Display shows "MODO 2 SELECCIONADO"
- ✅ System positions at home
- ✅ Ready for start

#### 4.2 Start and Observe

1. **Click "Start"** button in simulator
2. **Watch timing**: Motor should move faster than Mode 1

**Expected Result**:

- ✅ Linear motor moves 380 steps (longer than Mode 1)
- ✅ Movement is FASTER (velocidadLineal2 = 7000 vs 3000)
- ✅ Performs 400 rotations in level 1
- ✅ Performs 800 rotations in level 2
- ✅ Counter displays correctly

---

## **SCENARIO 5: Automatic Mode - Mode 3**

### Configuration (Mode 3)

- Level 1: 500 rotations
- Level 2: 1000 rotations
- Linear speed: 3200
- Steps level 1: 380
- Steps level 2: 80

### Steps

1. **Select Mode 3**
2. **Start cycle**
3. **Verify**: 500 rotations in level 1, 1000 in level 2
4. **Verify**: Speed is 3200 (medium speed)

**Expected Results**: Similar to modes 1 and 2, but with Mode 3 parameters

---

## **SCENARIO 6: Automatic Mode - Mode 4**

### Configuration (Mode 4)

- Level 1: 400 rotations
- Level 2: 800 rotations
- Linear speed: 3200
- Steps level 1: 380
- Steps level 2: 80

### Steps

1. **Select Mode 4**
2. **Start cycle**
3. **Verify**: 400 rotations in level 1, 800 in level 2

**Expected Results**: Similar pattern with Mode 4 specific parameters

---

## **SCENARIO 7: Automatic Mode - Mode 5**

### Configuration (Mode 5)

- Level 1: 50 rotations (SHORTEST)
- Level 2: 20 rotations (SHORTEST)
- Linear speed: 7000 (FASTEST)
- Steps level 1: 380
- Steps level 2: 80

### Steps

1. **Select Mode 5**
2. **Start cycle**
3. **Verify**: Quickest mode - only 50 + 20 rotations

**Expected Results**: Fastest and shortest cycle

---

## **SCENARIO 8: Emergency Stop During Execution**

### Story

_"During automatic operation, the operator notices something wrong and must stop immediately."_

### Steps

#### 8.1 Stop During Level 1

1. **Start any mode** (Mode 1 for example)
2. **Wait** until level 1 is executing (rotations ongoing)
3. **In Simulator UI**: Click **"Stop (GPIO 22)"** button

**Expected Result**:

- ✅ All motors stop IMMEDIATELY
- ✅ Display shows "EN PAUSA" (Paused)
- ✅ Position is maintained
- ✅ Rotation counter stays at current value

#### 8.2 Resume After Stop

1. **Wait a few seconds**
2. **Click "Start"** button again

**Expected Result**:

- ✅ 2-second delay before resuming
- ✅ Cycle continues from where it stopped
- ✅ Counter continues incrementing
- ✅ Motors resume with correct direction

#### 8.3 Stop During Level 2

1. **Let cycle reach level 2**
2. **Press Stop** button

**Expected Result**:

- ✅ Motors stop immediately
- ✅ System pauses
- ✅ Can resume with Start button

---

## **SCENARIO 9: Safety Switch Protection**

### Story

_"The safety guard is opened during operation. The machine must stop immediately for safety."_

### Steps

#### 9.1 Safety Switch During Manual Mode

1. **Enter manual mode**
2. **Move joystick** to start linear movement
3. **While moving**: Toggle **"Safety Switch (GPIO 6)"** OFF in simulator

**Expected Result**:

- ✅ All motors stop IMMEDIATELY
- ✅ Display shows "EN PAUSA"
- ✅ System waits for safety switch to be restored

#### 9.2 Restore Safety

1. **Toggle "Safety Switch"** back ON
2. **Press "Start"** button

**Expected Result**:

- ✅ System resumes operation
- ✅ 2-second delay before starting
- ✅ Manual mode continues normally

#### 9.3 Safety Switch During Automatic Cycle

1. **Start Mode 1**
2. **During execution**: Toggle **"Safety Switch"** OFF

**Expected Result**:

- ✅ All motors stop immediately
- ✅ Cannot continue until safety switch restored
- ✅ After restoring + pressing Start, cycle continues

---

## **SCENARIO 10: Reset During Execution**

### Story

_"The operator realizes wrong material was loaded and needs to abort the cycle completely."_

### Steps

#### 10.1 Reset During Cycle

1. **Start any automatic mode**
2. **During execution**: Click **"Reset (GPIO 17)"** button

**Expected Result**:

- ✅ Cycle aborts immediately
- ✅ All motors stop
- ✅ System returns to home position
- ✅ Display returns to mode selection (page 1)
- ✅ All counters reset to 0

#### 10.2 Verify Clean State

1. **Check all values** are reset
2. **Select a mode** again

**Expected Result**:

- ✅ System behaves as if freshly powered on
- ✅ Can start new cycle normally

---

## **SCENARIO 11: Multiple Cycles in Succession**

### Story

_"The operator processes multiple workpieces one after another."_

### Steps

#### 11.1 First Cycle

1. **Select Mode 1**
2. **Complete full cycle** (let it finish naturally)
3. **At completion**: Press **"Reset"**

**Expected Result**:

- ✅ Cycle completes successfully
- ✅ System returns to home

#### 11.2 Second Cycle - Same Mode

1. **Select Mode 1 again**
2. **Start new cycle**

**Expected Result**:

- ✅ Cycle runs identically to first
- ✅ No carry-over from previous cycle
- ✅ Counter starts from 0

#### 11.3 Third Cycle - Different Mode

1. **After second cycle**: Press **"Reset"**
2. **Select Mode 3** instead
3. **Start cycle**

**Expected Result**:

- ✅ Mode 3 parameters are used
- ✅ Different speeds and counts
- ✅ No interference from previous modes

---

## **SCENARIO 12: Limit Switch Edge Cases**

### Story

_"Testing boundary conditions with limit switches."_

### Steps

#### 12.1 Home Limit During Automatic Cycle

1. **Start Mode 1**
2. **During backward movement**: Trigger **"Home Limit"** ON

**Expected Result**:

- ✅ Motor stops
- ✅ May cause cycle interruption
- ✅ System should handle gracefully

#### 12.2 Final Limit During Automatic Cycle

1. **Start Mode 1**
2. **During forward movement**: Trigger **"Final Limit"** ON

**Expected Result**:

- ✅ Motor stops if limit reached
- ✅ System should handle safely

---

## 📊 Test Completion Checklist

After completing all scenarios, verify:

### ✅ Manual Mode

- [ ] Joystick left/right/center all work
- [ ] Tala button toggles drill motor
- [ ] Home limit protection works
- [ ] Final limit protection works
- [ ] Can enter and exit manual mode

### ✅ Automatic Modes

- [ ] Mode 1: 100 + 1000 rotations
- [ ] Mode 2: 400 + 800 rotations
- [ ] Mode 3: 500 + 1000 rotations
- [ ] Mode 4: 400 + 800 rotations
- [ ] Mode 5: 50 + 20 rotations (fastest)

### ✅ Safety Features

- [ ] Stop button pauses execution
- [ ] Start button resumes after stop
- [ ] Safety switch stops all motors
- [ ] Reset aborts and returns to home
- [ ] Limit switches prevent overtravel

### ✅ Timing and Sequences

- [ ] 2-second delay before drill starts
- [ ] 1-second delays between phases
- [ ] Counters update correctly
- [ ] Display messages are correct

---

## 🐛 Common Issues and Solutions

### Issue: Motors don't move

**Solution**: Check safety switch is ON (GPIO 6 = 1)

### Issue: Home sequence fails

**Solution**: Ensure Home Limit (GPIO 13) can be triggered

### Issue: Cycle doesn't start

**Solution**: Verify mode is selected and Start button is pressed

### Issue: Stop button doesn't work

**Solution**: Ensure GPIO 22 is being monitored correctly

### Issue: Display doesn't update

**Solution**: Check if Nextion serial communication is simulated

---

## 📝 Notes for Testers

1. **Simulator Activity Log**: Watch this closely - it shows all GPIO changes
2. **Timing**: Some operations have built-in delays (2 seconds, 1 second)
3. **Button Timing**: Hold buttons for ~1 second to ensure detection
4. **Counter Validation**: Manually count first few rotations to verify accuracy
5. **Speed Verification**: Mode 2 and 5 should visibly move faster
6. **Multiple Tests**: Run each scenario at least twice to confirm repeatability

---

## ✅ Success Criteria

A successful test means:

- ✅ All motors respond correctly to commands
- ✅ Limit switches provide protection
- ✅ Safety systems work immediately
- ✅ Counters are accurate
- ✅ All 5 modes execute with correct parameters
- ✅ Manual mode is fully controllable
- ✅ System can be stopped and resumed
- ✅ Reset function works at any time

---

**Testing Complete!** 🎉

Document any failures or unexpected behavior for debugging.
