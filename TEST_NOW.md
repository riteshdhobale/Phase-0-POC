## 🔧 SCANNER FIXED - Test Instructions

### ✅ What Was Fixed
The scanner was **crashing** because of a bleak library issue:
- **Error:** `'BLEDevice' object has no attribute 'rssi'`
- **Fix:** Updated to use `advertisement_data.rssi` instead
- **Git commit:** 20d0079

---

## 📱 ON RASPBERRY PI - DO THIS NOW:

### 1️⃣ Stop the current scanner (if running):
Press **Ctrl+C** in the Pi terminal

### 2️⃣ Pull latest code:
```bash
cd ~/Downloads/Phase-0-POC-main
git pull origin main
```

### 3️⃣ Restart the scanner:
```bash
cd raspberry-pi
python scanner.py
```

### ✅ You should see:
```
🚂 RAILWAY POC - RASPBERRY PI BLE SCANNER
==========================================================
✓ Cleanup handlers registered (SIGINT, SIGTERM, SIGQUIT, exit)
  Press Ctrl+C to stop gracefully

📡 Testing backend connection...
✅ Backend is reachable at http://192.168.31.187:8000

⏱️  Starting BLE proximity detection...

🔍 Starting BLE scanner...
📡 RSSI threshold: -70 dBm
⏱️  Exit delay: 10 seconds
🌐 Backend: http://192.168.31.187:8000
============================================================

📡 Scanning for BLE devices...

🔍 Scan found 3 BLE device(s)
```

---

## 🧪 TESTING STEPS:

### 1. **Verify Phone BLE is Active:**
- Open the Railway app on your phone
- You should see notification: "Railway BLE Service Active"
- If not, close and reopen the app

### 2. **Bring Phone Close to Raspberry Pi** (within 1 meter):

**Expected scanner output:**
```
🔍 Scan found 3 BLE device(s)
   📱 Device: XX:XX:XX:XX:XX:XX | RSSI: -65 dBm
      Service Data UUIDs: [UUID('0000fff0-0000-1000-8000-00805f9b34fb')]
🔍 Checking device: XX:XX:XX:XX:XX:XX
   🔑 Service UUID: 0000fff0-0000-1000-8000-00805f9b34fb
   📦 Service data: b'RAIL_USER::fa7d7378-3e7a-4b66-ac79-ea520b446192'
   📝 Decoded payload: RAIL_USER::fa7d7378-3e7a-4b66-ac79-ea520b446192
   ✅ Found user in service_data: fa7d7378...

🚶 NEW USER DETECTED
   User ID: fa7d7378...
   Device: Unknown
   RSSI: -65 dBm
   Time: 14:30:22

✅ Journey started for user fa7d7378...
```

**Expected phone app behavior:**
- Shows "Journey Active" message
- Shows your station name
- Wallet balance visible but no deduction yet

### 3. **Walk Away From Raspberry Pi** (more than 3 meters):

**After 10 seconds, scanner output:**
```
👋 User fa7d7378... has exited (not seen for 10.2 seconds)
✅ Journey ended for user fa7d7378... - Fare: ₹5
```

**Expected phone app behavior:**
- Shows "Journey Ended" message
- Wallet balance decreased by ₹5
- Shows fare deduction notification

---

## 🎯 SUCCESS CRITERIA:

✅ Scanner runs without "rssi" error  
✅ Scanner detects phone when nearby  
✅ Journey starts when phone approaches  
✅ Phone shows "Journey Active"  
✅ Journey ends when phone leaves for 10 seconds  
✅ Phone shows fare deduction (₹5)  
✅ Wallet balance decreases correctly  

---

## 🐛 If Still Not Working:

### Problem: Scanner doesn't detect phone
**Solution:**
1. Make sure phone and Pi are **very close** (< 1 meter)
2. Check phone notification shows BLE is active
3. Temporarily increase RSSI threshold in scanner.py:
   ```python
   RSSI_THRESHOLD = -90  # Line 21
   ```

### Problem: Scanner detects phone but journey doesn't start
**Check backend logs on Mac:**
```bash
# Should show:
POST /journey_start?user_id=fa7d7378... HTTP/1.1" 200 OK
```

If not appearing, check network connectivity:
```bash
# On Raspberry Pi:
curl http://192.168.31.187:8000/
# Should return: {"message":"Railway POC Backend is running"}
```

### Problem: Journey starts but doesn't end
- Wait **full 10 seconds** after walking away
- Check scanner output shows "User has exited"
- Check backend logs show `POST /journey_end`

---

## 📊 Current System Status:

✅ **MacBook Backend:** Running on http://192.168.31.187:8000  
✅ **Android Phone:** Wallet working, BLE advertising active  
✅ **Scanner Code:** Fixed (commit 20d0079)  
⏳ **Raspberry Pi:** Needs to pull latest code and restart  

**Your user ID:** `fa7d7378-3e7a-4b66-ac79-ea520b446192`  
**Current wallet:** ₹200 (after add funds test)

---

**🎯 Next Action:** Pull latest code on Raspberry Pi and restart scanner!
