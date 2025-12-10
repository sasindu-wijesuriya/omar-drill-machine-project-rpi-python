#!/bin/bash

# RPi Motor Control - Quick Test Script
# Tests basic functionality and demonstrates enhanced logging

API="http://localhost:5000"

echo "=========================================="
echo "  RPi Motor Control - Test Suite"
echo "=========================================="
echo ""

# Function to show logs for last command
show_logs() {
    echo "📋 Recent logs:"
    sudo journalctl -u rpi-motor-control.service -n 10 --no-pager | tail -8 | sed 's/^/   /'
    echo ""
}

# Test 1: Select Logic A
echo "Test 1: Selecting Logic A..."
curl -s -X POST $API/api/select_logic -H "Content-Type: application/json" -d '{"logic": "A"}' | python3 -m json.tool
sleep 1
show_logs

# Test 2: Select Logic B
echo "Test 2: Selecting Logic B..."
curl -s -X POST $API/api/select_logic -H "Content-Type: application/json" -d '{"logic": "B"}' | python3 -m json.tool
sleep 1
show_logs

# Test 3: Press Reset/Home Button
echo "Test 3: Pressing Reset/Home button..."
curl -s -X POST $API/api/gpio/button_press -H "Content-Type: application/json" -d '{"pin": 17, "duration": 100}' | python3 -m json.tool
sleep 1
show_logs

# Test 4: Set Mode Switch
echo "Test 4: Setting Mode Switch to LOW..."
curl -s -X POST $API/api/gpio/write -H "Content-Type: application/json" -d '{"pin": 6, "value": 0}' | python3 -m json.tool
sleep 1
show_logs

# Test 5: Press Start Button
echo "Test 5: Pressing Start button..."
curl -s -X POST $API/api/gpio/button_press -H "Content-Type: application/json" -d '{"pin": 27, "duration": 100}' | python3 -m json.tool
sleep 1
show_logs

# Test 6: Trigger Home Limit Switch
echo "Test 6: Triggering Home Limit Switch..."
curl -s -X POST $API/api/gpio/write -H "Content-Type: application/json" -d '{"pin": 13, "value": 1}' | python3 -m json.tool
sleep 1
show_logs

# Test 7: Press Stop Button
echo "Test 7: Pressing Stop button..."
curl -s -X POST $API/api/gpio/button_press -H "Content-Type: application/json" -d '{"pin": 22, "duration": 100}' | python3 -m json.tool
sleep 1
show_logs

# Test 8: GPIO Status Check
echo "Test 8: Checking GPIO Status..."
curl -s $API/api/gpio/status | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Total pins: {len(data['pins'])}\"); [print(f\"  - GPIO {p['pin']}: {p['name']} = {p['value_display']}\") for p in data['pins'][:5]]"
echo ""

echo "=========================================="
echo "  Test Suite Complete!"
echo "=========================================="
echo ""
echo "📊 View full logs with:"
echo "   sudo journalctl -u rpi-motor-control.service -f"
echo ""
echo "🌐 Web interfaces:"
echo "   Main Dashboard:  http://localhost:5000"
echo "   GPIO Monitor:    http://localhost:5000/gpio"
echo "   Engineer Menu:   http://localhost:5000/engineer"
echo ""
