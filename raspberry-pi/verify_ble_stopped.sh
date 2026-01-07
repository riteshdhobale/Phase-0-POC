#!/bin/bash

# Script to verify BLE has stopped on macOS

echo "🔍 Checking BLE Status on macOS..."
echo "=================================="
echo ""

# Check if Python BLE scanner is running
echo "1️⃣  Checking for active Python BLE processes..."
PYTHON_BLE=$(ps aux | grep -E "python.*scanner\.py|bleak" | grep -v grep)
if [ -z "$PYTHON_BLE" ]; then
    echo "✅ No Python BLE scanner processes found"
else
    echo "⚠️  Found running BLE processes:"
    echo "$PYTHON_BLE"
fi
echo ""

# Check Bluetooth power state
echo "2️⃣  Checking Bluetooth power state..."
BT_POWER=$(system_profiler SPBluetoothDataType 2>/dev/null | grep -i "state" | head -1)
if [ -z "$BT_POWER" ]; then
    echo "ℹ️  Could not determine Bluetooth state (may require sudo)"
else
    echo "$BT_POWER"
fi
echo ""

# Check for active Bluetooth connections
echo "3️⃣  Checking active Bluetooth connections..."
BT_CONNECTIONS=$(system_profiler SPBluetoothDataType 2>/dev/null | grep -A 5 "Connected:")
if [ -z "$BT_CONNECTIONS" ]; then
    echo "✅ No active Bluetooth connections detected"
else
    echo "$BT_CONNECTIONS"
fi
echo ""

# Check system Bluetooth info
echo "4️⃣  Checking Bluetooth controller state..."
BT_CONTROLLER=$(system_profiler SPBluetoothDataType 2>/dev/null | grep -E "Discoverable|Connectable" | head -2)
echo "$BT_CONTROLLER"
echo ""

# Check for lingering async/event loop processes
echo "5️⃣  Checking for lingering Python asyncio processes..."
ASYNCIO_PROCS=$(ps aux | grep -E "python.*asyncio|Python.*uvloop" | grep -v grep)
if [ -z "$ASYNCIO_PROCS" ]; then
    echo "✅ No lingering Python asyncio processes found"
else
    echo "⚠️  Found asyncio processes:"
    echo "$ASYNCIO_PROCS"
fi
echo ""

# Check CPU usage by Python
echo "6️⃣  Checking Python CPU usage..."
PYTHON_CPU=$(ps aux | grep python | grep -v grep | awk '{if($3>1.0) print}')
if [ -z "$PYTHON_CPU" ]; then
    echo "✅ No high CPU usage from Python processes"
else
    echo "⚠️  Python processes using CPU:"
    echo "$PYTHON_CPU"
fi
echo ""

echo "=================================="
echo "✅ BLE Verification Complete"
echo ""
echo "💡 To fully reset Bluetooth on macOS:"
echo "   1. Toggle Bluetooth OFF in System Preferences"
echo "   2. Wait 5 seconds"
echo "   3. Toggle Bluetooth ON again"
echo ""
echo "🔋 Battery impact:"
echo "   - Open Activity Monitor → Energy tab"
echo "   - Look for 'Python' processes with high 'Energy Impact'"
echo ""
