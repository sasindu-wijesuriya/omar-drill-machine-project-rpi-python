# Understanding GPIO Simulator and Motor Control

## Why Motors Appear "Not Moving" in Simulator

### The Issue

When you clicked "Select Mode 1", the system **IS working correctly** but the stepper motor pulses are happening so fast that:

1. **HTTP Requests are Overwhelming**: Stepper motors pulse at rates of 500-10,000 Hz (pulses per second)
2. **Each pulse** would require an HTTP request to the simulator
3. **The UI can't update** fast enough to show individual pulses
4. **Logs show activity** but GPIO indicators don't flash visibly

### The Fix Applied

I've updated the simulator to:

1. **Track Pulse Activity**: Count pulses instead of trying to display each one
2. **Show Pulsing Animation**: PWM pins show a "pulsing glow" effect when active
3. **Throttle WebSocket Updates**: Only send important state changes, not every pulse
4. **Activity Indicators**: LED indicators will glow and pulse when motors are running

## How to Verify It's Working

### Method 1: Check the Logs

In the Motor Control terminal, you should see:

```
Finding home position
Linear motor moving toward home
```

### Method 2: Watch Direction Pin

- **GPIO 23 (dir1)** changes value → Motor direction is changing ✓
- **GPIO 18 (pulsos1)** LED glows with pulsing animation → Motor is stepping ✓

### Method 3: Monitor Simulator

After the update, you'll see:

- **Pulse Count** in activity log
- **Glowing LED indicators** for active motors
- **Pulsing animation** on GPIO 18 and GPIO 24 when motors run

## What Should Happen in Scenario 1.2

1. **Select Logic A** → System loads configuration ✓
2. **Click Mode 1** → System initiates home sequence ✓
3. **Motor moves toward home**:

   - GPIO 23 (dir1) = **1** (toward home direction)
   - GPIO 18 (pulsos1) **glows and pulses** (motor stepping)
   - Activity log shows "Finding home"

4. **When you toggle "Home Limit"** switch:
   - Motor stops
   - Motor reverses slightly (425 steps)
   - System displays "Ready"

## Current Status

**Your system IS working!** The motor controller is:

- ✅ Connected to simulator
- ✅ Sending GPIO commands
- ✅ Executing home sequence
- ✅ Using correct mock library

The visualization just needed improvement to show the high-speed pulses.

## Next Steps

1. **Restart the simulator** to apply the new changes
2. **Try Scenario 1.2 again**
3. **Look for the pulsing glow** on motor LEDs
4. **Check activity log** for pulse counts

## Technical Details

### Why HTTP is "Slow" for PWM

- Real GPIO: **Direct memory writes** (nanoseconds)
- Simulator: **HTTP requests** (~1-10 milliseconds each)
- Motor needs: **500-10,000 pulses/second**
- HTTP can handle: **~100-1000 requests/second**

### The Solution

Instead of trying to send every pulse over HTTP (impossible), we:

1. **Track activity** server-side
2. **Show aggregate status** (is motor running? pulse count)
3. **Use visual indicators** (glowing, pulsing animations)
4. **Throttle updates** to what humans can actually see

This gives you **functional testing** of logic without needing real hardware!
