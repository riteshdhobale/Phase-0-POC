# 🔧 Scanner Fixed - RSSI Error Resolved

## What Was The Problem?
The scanner was **crashing** with:
```
❌ Scan error: 'BLEDevice' object has no attribute 'rssi'
```

This happened because the **bleak library changed** how it provides RSSI data in newer versions.

## What Was Fixed?

### 1. **Changed Scanner Discovery Method**
```python
# OLD (broken):
devices = await active_scanner.discover(timeout=SCAN_INTERVAL)
for device in devices:
    rssi = device.rssi  # ❌ This doesn't exist!

# NEW (fixed):
devices_dict = await active_scanner.discover(timeout=SCAN_INTERVAL, return_adv=True)
for address, (device, advertisement_data) in devices_dict.items():
    rssi = advertisement_data.rssi  # ✅ This works!
```

### 2. **Updated extract_user_id() Function**
```python
# OLD:
def extract_user_id(device):
    # Tried to access device.metadata (doesn't exist)

# NEW:
def extract_user_id(device, advertisement_data):
    # Now uses advertisement_data.service_data
    # And advertisement_data.manufacturer_data
```

### 3. **Better Debug Logging**
- Shows exactly what service UUIDs are received
- Shows the actual payload data
- Shows when user_id extraction succeeds or fails

## 📋 Next Steps on Raspberry Pi

**Pull the latest code:**
```bash
cd ~/Downloads/Phase-0-POC-main/raspberry-pi
git pull origin main
```

**Run the updated scanner:**
```bash
python scanner.py
```

## ✅ What Should Happen Now

1. Scanner starts without errors
2. Shows devices detected with RSSI values
3. When phone is nearby, shows:
   ```
   🔍 Checking device: XX:XX:XX:XX:XX:XX
      🔑 Service UUID: 0000fff0-...
      📦 Service data: b'RAIL_USER::fa7d...'
      📝 Decoded payload: RAIL_USER::fa7d7378-3e7a-4b66-ac79-ea520b446192
      ✅ Found user in service_data: fa7d7378...
   
   🚶 NEW USER DETECTED
      User ID: fa7d7378...
      Device: Unknown
      RSSI: -65 dBm
      Time: 14:23:45
   ```

4. Backend receives `journey_start` request
5. Wallet shows "Journey Active"
6. When you walk away, scanner waits 10 seconds, then calls `journey_end`
7. Fare is deducted from wallet

## 🐛 If Still Not Working

1. **Check phone BLE is actually advertising:**
   - Notification should show "Railway BLE Service Active"
   - Try toggling it off and on

2. **Check phone is close enough:**
   - Should be within 2-3 meters of Raspberry Pi
   - RSSI threshold is -70 dBm

3. **Check backend logs:**
   - Should see `POST /journey_start` requests appearing

4. **Increase RSSI threshold** (for testing):
   ```python
   RSSI_THRESHOLD = -90  # Allow weaker signals
   ```
