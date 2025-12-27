# Android App Setup Guide

## Prerequisites

1. **Download Android Studio**
   - Visit: https://developer.android.com/studio
   - Download: Android Studio Hedgehog (2023.1.1) or newer
   - Choose: Apple Silicon (M1) version for Mac
   - Size: ~8GB download, ~25GB installed

2. **Install Android Studio**
   - Open the downloaded DMG file
   - Drag Android Studio to Applications folder
   - First launch will download Android SDK (~10GB)
   - Accept all licenses

## Project Setup

### Step 1: Create New Project

1. Open Android Studio
2. Click "New Project"
3. Select "Empty Activity"
4. Configure:
   - **Name:** Railway POC
   - **Package name:** com.railway.poc
   - **Save location:** `/Users/ritesh/Phase-0 POC/android-app`
   - **Language:** Kotlin
   - **Minimum SDK:** API 21 (Android 5.0)
5. Click "Finish"

### Step 2: Replace Files

Once the project is created, replace these files with the provided code:

1. **AndroidManifest.xml**
   - Location: `app/src/main/AndroidManifest.xml`
   - Copy from: `/Users/ritesh/Phase-0 POC/android-app/AndroidManifest.xml`

2. **MainActivity.kt**
   - Location: `app/src/main/java/com/railway/poc/MainActivity.kt`
   - Copy from: `/Users/ritesh/Phase-0 POC/android-app/MainActivity.kt`

3. **BleAdvertisingService.kt**
   - Location: `app/src/main/java/com/railway/poc/` (create new file)
   - Copy from: `/Users/ritesh/Phase-0 POC/android-app/BleAdvertisingService.kt`

4. **activity_main.xml**
   - Location: `app/src/main/res/layout/activity_main.xml`
   - Copy from: `/Users/ritesh/Phase-0 POC/android-app/res/layout/activity_main.xml`

5. **build.gradle (app level)**
   - Location: `app/build.gradle`
   - Copy from: `/Users/ritesh/Phase-0 POC/android-app/build.gradle`

### Step 3: Update Backend IP

Open `MainActivity.kt` and change line 45:

```kotlin
private val BACKEND_URL = "http://192.168.31.187:8000"
```

Replace `192.168.31.187` with your MacBook's WiFi IP (already set correctly).

### Step 4: Sync Project

1. Click "Sync Now" banner (appears after file changes)
2. Wait for Gradle sync to complete (~2 minutes)
3. Fix any import errors (Android Studio auto-fixes most)

## Build & Install

### Step 5: Connect Android Phone

1. **Enable Developer Options on phone:**
   - Settings → About Phone → Tap "Build Number" 7 times
   - Go back → Developer Options → Enable "USB Debugging"

2. **Connect phone to MacBook via USB cable**

3. **Allow USB Debugging:**
   - Phone will show popup "Allow USB debugging?"
   - Check "Always allow from this computer"
   - Click "OK"

4. **Verify connection in Android Studio:**
   - Top toolbar should show your phone model
   - Example: "Samsung Galaxy S21" or "Pixel 6"

### Step 6: Build APK

1. Click green "Run" button (▶️) in Android Studio toolbar
2. Select your connected phone from dropdown
3. Click "OK"
4. Wait for build (~3-5 minutes first time)
5. App will auto-install and launch on phone

## Testing

### Step 7: Test App Functions

1. **User Registration:**
   - App should auto-register on first launch
   - User ID appears as "User ID: abc12345..."
   - Wallet shows ₹100

2. **Add Funds:**
   - Tap "Add ₹100" button
   - Balance should increase to ₹200
   - Toast message: "✅ ₹100 Added Successfully!"

3. **Start BLE Advertising:**
   - Tap "Start BLE Advertising"
   - Grant all permissions (Bluetooth, Location, Notifications)
   - Persistent notification appears: "Broadcasting User ID via BLE"
   - Button changes to "Stop BLE Advertising"

4. **Wallet Polling:**
   - Balance updates every 5 seconds
   - "Journey: NOT ACTIVE" initially
   - When Pi detects phone, journey becomes "ACTIVE"
   - When Pi detects exit, fare deducts automatically

## Troubleshooting

### Build Errors

**Error: "SDK not found"**
- Solution: Android Studio → Preferences → Appearance & Behavior → System Settings → Android SDK
- Install Android 14.0 (API 34)

**Error: "Kotlin not configured"**
- Solution: Tools → Kotlin → Configure Kotlin in Project
- Select "All modules"

**Error: "CardView not found"**
- Solution: Already added in build.gradle, just sync again

### Runtime Errors

**App crashes on launch:**
- Check Logcat in Android Studio (bottom panel)
- Look for red error messages
- Common issue: Backend URL unreachable
- Fix: Ensure MacBook backend is running

**BLE advertising fails:**
- Check phone Bluetooth is ON
- Check permissions granted (Settings → Apps → Railway POC → Permissions)
- Some phones don't support BLE advertising (very rare)

**Wallet shows error:**
- Check MacBook and phone on same WiFi network
- Test backend: Open `http://192.168.31.187:8000/docs` in phone browser
- Should show FastAPI Swagger UI

## Next Steps

Once app is working:
1. Keep backend running on MacBook
2. Keep app running on phone with BLE advertising ON
3. Move to Raspberry Pi setup (Day 5-7)
4. Pi will detect your phone's BLE signal

## File Structure Reference

```
android-app/
├── app/
│   ├── src/
│   │   └── main/
│   │       ├── java/com/railway/poc/
│   │       │   ├── MainActivity.kt
│   │       │   └── BleAdvertisingService.kt
│   │       ├── res/
│   │       │   └── layout/
│   │       │       └── activity_main.xml
│   │       └── AndroidManifest.xml
│   └── build.gradle
├── build.gradle (project level)
└── settings.gradle
```

## Backend Integration Points

- **POST /register_user** → Called on first app launch
- **GET /wallet_balance** → Polled every 5 seconds
- **POST /add_funds** → Called when "Add ₹100" tapped
- **BLE Payload:** `RAIL_USER::<user_id>` → Detected by Pi
