# Phase-0 POC — Quick Testing Guide

## Test Sequence (After All Setup Complete)

### 1. Backend Test (MacBook)

```bash
# Terminal 1: Start backend
cd "/Users/ritesh/Phase-0 POC/backend"
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

Open browser: `http://localhost:8000/docs`
- Should see FastAPI Swagger UI
- 5 endpoints visible

### 2. Phone App Test (Android)

**Prerequisites:**
- App installed via Android Studio
- Phone connected to same WiFi as MacBook
- Bluetooth enabled on phone

**Test Steps:**

1. **Launch app**
   - Should auto-register
   - Shows: "User ID: abc12345..."
   - Shows: "₹100" wallet balance

2. **Test Add Funds**
   - Tap "Add ₹100" button
   - Balance should change to ₹200
   - Toast: "✅ ₹100 Added Successfully!"

3. **Start BLE Advertising**
   - Tap "Start BLE Advertising"
   - Grant all permissions (Bluetooth, Location, Notifications)
   - Notification appears: "Broadcasting User ID via BLE"
   - Button becomes "Stop BLE Advertising"

### 3. Raspberry Pi Scanner Test

**On MacBook, open new terminal:**

```bash
# SSH into Pi
ssh pi@railway-poc.local

# Start scanner
cd ~/railway-poc
python3 scanner.py
```

**Expected output:**
```
============================================================
🚂 RAILWAY POC - RASPBERRY PI BLE SCANNER
============================================================

🔌 Testing backend connection...
✅ Backend is reachable at http://192.168.31.187:8000

✅ Starting BLE proximity detection...

🔍 Starting BLE scanner...
📊 Currently tracking 0 user(s)
```

### 4. Full Integration Test

**Test A: Entry Detection**

1. **Hold phone near Raspberry Pi** (within 2-3 meters)
2. **Pi terminal should show:**
   ```
   🚶 NEW USER DETECTED
      User ID: abc12345...
      RSSI: -65 dBm
      Time: 14:30:45
   
   ✅ Journey started for user abc12345...
      Journey ID: def67890...
   ```

3. **Phone app should show:**
   - "Journey: ACTIVE"
   - Wallet still ₹200 (no fare yet)

**Test B: Exit Detection**

1. **Walk away with phone** (more than 3-4 meters from Pi)
2. **Wait 10 seconds**
3. **Pi terminal should show:**
   ```
   🚪 USER EXITED
      User ID: abc12345...
      Out of range for: 11s
   
   🎫 Journey ended for user abc12345...
      Fare deducted: ₹20
      Remaining balance: ₹180
   ```

4. **Phone app should show:**
   - "Journey: NOT ACTIVE"
   - Wallet: ₹180
   - Toast: "⚠️ Fare Deducted: ₹20"

**Test C: Multiple Journeys**

1. Walk near Pi again → journey starts
2. Walk away → journey ends, fare deducted (₹160)
3. Repeat → each time ₹20 deducted
4. Balance: ₹200 → ₹180 → ₹160 → ₹140...

**Test D: Add Funds**

1. Tap "Add ₹100" in app
2. Balance increases
3. Continue testing journeys

## Expected Behavior Summary

| Action | Backend | Phone | Pi |
|--------|---------|-------|-----|
| App launches | POST /register_user | Shows User ID, ₹100 | - |
| Tap "Add Funds" | POST /add_funds | Balance +₹100 | - |
| Start BLE | - | Notification appears | - |
| Phone near Pi | POST /journey_start | Journey: ACTIVE | "NEW USER DETECTED" |
| Phone away 10s | POST /journey_end | Balance -₹20, Toast | "USER EXITED" |

## Common Issues & Fixes

### Phone Not Detected by Pi

**Check:**
- [ ] Phone BLE advertising is ON (notification visible)
- [ ] Phone and Pi on same WiFi network
- [ ] Pi scanner running (no errors in terminal)
- [ ] Phone within 2-3 meters of Pi

**Debug:**
```bash
# On Pi: Manual BLE scan
sudo hcitool lescan
# Should see phone's Bluetooth MAC address
# Press Ctrl+C to stop

# Check Bluetooth interface
hciconfig
# Should show: hci0 UP RUNNING
```

### Journey Doesn't Start

**Check:**
- [ ] Backend running on MacBook
- [ ] Pi can reach backend: `curl http://192.168.31.187:8000/`
- [ ] Scanner shows "Backend is reachable"

**Debug on Pi:**
```bash
# Test backend directly
curl -X POST "http://192.168.31.187:8000/journey_start?user_id=test123"

# Should return JSON with journey_id
```

### Wallet Doesn't Update

**Check:**
- [ ] Phone has internet connection (same WiFi)
- [ ] Backend URL in app matches MacBook IP
- [ ] Backend running and accessible

**Debug in app:**
- Check Android Logcat in Android Studio
- Look for network errors
- Verify wallet polling is running (updates every 5s)

### Fare Not Deducted on Exit

**Check:**
- [ ] Journey was started (phone detected by Pi first)
- [ ] Phone moved far enough away (>4 meters)
- [ ] Waited full 10 seconds out of range

**Debug on Pi terminal:**
- Look for "USER EXITED" message
- Check "Out of range for: Xs" — must be >10 seconds

## Demo Recording Checklist

Record video showing:

1. **MacBook backend terminal** (backend running)
2. **Phone app screen:**
   - User ID visible
   - Starting balance (e.g., ₹200)
   - Start BLE advertising
3. **Pi terminal** (scanner running)
4. **Walk near Pi with phone:**
   - Pi: "NEW USER DETECTED"
   - Pi: "Journey started"
   - Phone: "Journey: ACTIVE"
5. **Walk away with phone:**
   - Wait 10 seconds
   - Pi: "USER EXITED", "Journey ended", "Fare deducted: ₹20"
   - Phone: Balance changes ₹200 → ₹180
   - Phone: Toast "Fare Deducted ₹20"
6. **Tap Add Funds:**
   - Balance ₹180 → ₹280
   - Toast "✅ ₹100 Added Successfully!"
7. **Repeat journey** to show it works multiple times

## System Architecture Visualization

```
┌─────────────────┐
│  Android Phone  │
│  BLE Broadcast  │ ←── "RAIL_USER::<user_id>"
│  Wallet: ₹180   │
└────────┬────────┘
         │ WiFi (Poll balance every 5s)
         ↓
┌─────────────────┐      ┌──────────────────┐
│ Raspberry Pi 3  │←WiFi→│ MacBook (Backend)│
│ BLE Scanner     │      │ FastAPI + SQLite │
│ RSSI Detection  │      │ Port 8000        │
└─────────────────┘      └──────────────────┘
         │                         │
         │ HTTP POST               │ HTTP GET/POST
         ↓                         ↓
    journey_start()          wallet_balance()
    journey_end()            add_funds()
```

## Next Steps After Successful Test

1. ✅ Clean up code (if needed)
2. ✅ Add logging to files (optional)
3. ✅ Record professional demo video
4. ✅ Write 1-page POC summary document
5. ✅ Prepare Phase-1 proposal (mmWave radar integration)
6. ✅ Submit for grant funding

## Test Completion Criteria

Phase-0 POC is **COMPLETE** when:

- ✅ Backend running on MacBook with 5 working endpoints
- ✅ Android app registers users, polls wallet, shows balance
- ✅ BLE advertising works in background (foreground service)
- ✅ Pi detects phone BLE within configured range
- ✅ Journey starts automatically when phone detected
- ✅ Journey ends automatically when phone exits range
- ✅ Fare (₹20) deducts from wallet on exit
- ✅ Add Funds button increases wallet balance
- ✅ All components logged and auditable (SQLite database)
- ✅ Demo video recorded showing end-to-end flow

**Congratulations! Phase-0 POC proves:**
1. Identity binding (user_id persistence)
2. Journey lifecycle (start/end based on proximity)
3. Automated enforcement (fare deduction without manual intervention)
4. System auditability (all transactions logged)

Ready for Phase-1 (mmWave radar Safety Dome) grant application! 🎉
