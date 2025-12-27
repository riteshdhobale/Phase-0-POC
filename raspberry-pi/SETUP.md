# Raspberry Pi Setup Guide

## Hardware Requirements

✅ **Raspberry Pi 3 Model B** (you have this)
- Built-in Bluetooth 4.1 (BLE capable)
- Built-in WiFi

## Prerequisites

### Step 1: Flash Raspberry Pi OS

1. **Download Raspberry Pi Imager**
   - From another computer: https://www.raspberrypi.com/software/
   
2. **Flash SD Card**
   - Insert microSD card (16GB minimum)
   - Open Raspberry Pi Imager
   - Choose OS: **Raspberry Pi OS Lite (64-bit)** — No desktop needed
   - Choose Storage: Your SD card
   - Click gear icon (⚙️) for advanced options:
     - ✅ Set hostname: `railway-poc`
     - ✅ Enable SSH (use password authentication)
     - ✅ Set username: `pi`
     - ✅ Set password: (your choice)
     - ✅ Configure WiFi:
       - SSID: (your WiFi name)
       - Password: (your WiFi password)
       - Country: (your country code)
   - Click "Write"
   - Wait 5-10 minutes

3. **Boot Raspberry Pi**
   - Insert SD card into Pi
   - Connect power supply
   - Wait 2 minutes for first boot

### Step 2: Connect via SSH

**From your MacBook Terminal:**

```bash
# Find Pi IP address (if hostname doesn't work)
ping railway-poc.local

# OR use IP scanner
arp -a | grep -i "b8:27:eb\|dc:a6:32"

# SSH into Pi
ssh pi@railway-poc.local
# OR
ssh pi@<PI_IP_ADDRESS>

# Enter password you set earlier
```

## Software Setup

### Step 3: Update System

```bash
# Update package lists
sudo apt update

# Upgrade existing packages (optional but recommended)
sudo apt upgrade -y
```

### Step 4: Install Python & BLE Dependencies

```bash
# Install Python 3 and pip (should already be installed)
sudo apt install python3 python3-pip -y

# Install Bluetooth tools
sudo apt install bluetooth bluez bluez-tools -y

# Install system libraries for bleak
sudo apt install libglib2.0-dev -y

# Enable Bluetooth service
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Check Bluetooth status
sudo systemctl status bluetooth
# Should show "active (running)"
```

### Step 5: Fix Bluetooth Permissions

```bash
# Allow non-root access to Bluetooth
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))

# Disable ModemManager (conflicts with Bluetooth)
sudo systemctl disable ModemManager
sudo systemctl stop ModemManager
```

### Step 6: Install Python Dependencies

```bash
# Create project directory
mkdir -p ~/railway-poc
cd ~/railway-poc

# Create requirements.txt (or copy from MacBook)
cat > requirements.txt << EOF
bleak==0.21.1
requests==2.31.0
EOF

# Install Python packages
pip3 install -r requirements.txt --break-system-packages

# Note: --break-system-packages flag is needed on Raspberry Pi OS Bookworm
```

### Step 7: Copy Scanner Script

**Option A: Copy from MacBook via SCP**

On your MacBook:
```bash
# Copy scanner script to Pi
scp "/Users/ritesh/Phase-0 POC/raspberry-pi/scanner.py" pi@railway-poc.local:~/railway-poc/

scp "/Users/ritesh/Phase-0 POC/raspberry-pi/trigger_violation.py" pi@railway-poc.local:~/railway-poc/
```

**Option B: Create file manually on Pi**

```bash
cd ~/railway-poc
nano scanner.py
# Paste content from scanner.py, then Ctrl+X, Y, Enter
```

### Step 8: Update Backend IP in Scanner

```bash
cd ~/railway-poc
nano scanner.py

# Change line 11:
BACKEND_URL = "http://192.168.31.187:8000"
# Replace with your MacBook's WiFi IP

# Save: Ctrl+X, Y, Enter
```

### Step 9: Test Backend Connection

```bash
# Test if Pi can reach MacBook backend
curl http://192.168.31.187:8000/

# Should return: {"status":"Railway POC Backend Running","version":"1.0"}
```

## Running the Scanner

### Step 10: Start Scanner

```bash
cd ~/railway-poc

# Run scanner
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
📡 RSSI threshold: -70 dBm
⏱️  Exit delay: 10 seconds
🌐 Backend: http://192.168.31.187:8000
============================================================

📊 Currently tracking 0 user(s)
```

### Step 11: Test with Phone

1. **On Android phone:**
   - Open Railway POC app
   - Tap "Start BLE Advertising"
   - Grant all permissions

2. **On Raspberry Pi terminal:**
   - Should see:
   ```
   🚶 NEW USER DETECTED
      User ID: abc12345...
      Device: Unknown
      RSSI: -65 dBm
      Time: 14:30:45
   
   ✅ Journey started for user abc12345...
      Journey ID: def67890...
   ```

3. **Walk away with phone:**
   - After 10 seconds out of range:
   ```
   🚪 USER EXITED
      User ID: abc12345...
      Time: 14:31:20
      Out of range for: 11s
   
   🎫 Journey ended for user abc12345...
      Fare deducted: ₹20
      Remaining balance: ₹80
   ```

4. **On phone:**
   - Wallet balance should update to ₹80
   - Toast: "⚠️ Fare Deducted: ₹20"

## Troubleshooting

### BLE Scanner Issues

**Error: "org.bluez.Error.NotReady: Resource Not Ready"**
```bash
# Restart Bluetooth service
sudo systemctl restart bluetooth
sudo hciconfig hci0 up

# Check Bluetooth interface
hciconfig
# Should show hci0 UP RUNNING
```

**Error: "Permission denied"**
```bash
# Fix Bluetooth permissions
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))
```

**No devices detected:**
```bash
# Test BLE scan manually
sudo hcitool lescan

# Should show nearby BLE devices
# Press Ctrl+C to stop
```

### Network Issues

**Cannot reach backend:**
```bash
# Check Pi is on same WiFi
ip addr show wlan0 | grep inet

# Should show IP in same subnet as MacBook (192.168.31.x)

# Ping MacBook
ping 192.168.31.187

# Test backend
curl http://192.168.31.187:8000/docs
```

**Pi can't connect to WiFi:**
```bash
# Check WiFi configuration
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

# Should contain:
network={
    ssid="YourWiFiName"
    psk="YourWiFiPassword"
}

# Restart WiFi
sudo systemctl restart networking
```

## Advanced Configuration

### Adjust RSSI Threshold

In `scanner.py`, line 14:
```python
RSSI_THRESHOLD = -70  # Change to -60 (closer) or -80 (wider range)
```

Values:
- **-60 dBm:** Very close (~1 meter) — strict proximity
- **-70 dBm:** Close (~2-3 meters) — recommended for POC
- **-80 dBm:** Wider range (~5-6 meters) — may detect users outside train

### Adjust Exit Delay

In `scanner.py`, line 18:
```python
EXIT_DELAY_SECONDS = 10  # Change to 5 (faster) or 15 (more forgiving)
```

Values:
- **5 seconds:** Quick exit detection (may have false exits)
- **10 seconds:** Balanced (recommended)
- **15 seconds:** Forgiving (handles temporary signal drops)

### Run Scanner on Boot (Optional)

```bash
# Create systemd service
sudo nano /etc/systemd/system/railway-scanner.service

# Add:
[Unit]
Description=Railway POC BLE Scanner
After=bluetooth.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/railway-poc
ExecStart=/usr/bin/python3 /home/pi/railway-poc/scanner.py
Restart=always

[Install]
WantedBy=multi-user.target

# Save and enable
sudo systemctl enable railway-scanner
sudo systemctl start railway-scanner

# Check status
sudo systemctl status railway-scanner

# View logs
sudo journalctl -u railway-scanner -f
```

## Testing Checklist

- [ ] Pi boots and connects to WiFi
- [ ] SSH connection works
- [ ] Bluetooth service running (`systemctl status bluetooth`)
- [ ] Backend reachable from Pi (`curl http://192.168.31.187:8000/`)
- [ ] Scanner starts without errors (`python3 scanner.py`)
- [ ] Phone BLE detected by Pi (see "NEW USER DETECTED")
- [ ] Journey starts successfully
- [ ] Walking away triggers journey end after 10 seconds
- [ ] Fare deducted (₹20) and shown on phone
- [ ] Wallet balance updates on phone app

## File Structure on Pi

```
~/railway-poc/
├── scanner.py              # Main BLE scanner script
├── trigger_violation.py    # Manual violation trigger (Phase-1)
├── requirements.txt        # Python dependencies
└── logs/                   # Optional: Add logging later
```

## Network Configuration

**Must be on same network:**
- MacBook: `192.168.31.187` (backend server)
- Raspberry Pi: `192.168.31.x` (scanner)
- Android Phone: `192.168.31.x` (app)

All three devices communicate over local WiFi.

## Next Steps After Setup

1. **Test full flow:**
   - MacBook backend running ✅
   - Phone app advertising BLE ✅
   - Pi scanner detecting and calling backend ✅
   - Fare auto-deduction working ✅

2. **Record demo video:**
   - Show all 3 devices
   - Walk into range → journey starts
   - Walk away → fare deducted
   - Press Add Funds → balance increases

3. **Prepare for Phase-1:**
   - Safety violation features
   - mmWave radar integration
   - Grant application ready

## Common Commands Reference

```bash
# Start scanner
cd ~/railway-poc && python3 scanner.py

# Stop scanner
Ctrl+C

# Check backend
curl http://192.168.31.187:8000/

# Check Bluetooth
sudo systemctl status bluetooth
hciconfig

# View Pi IP
hostname -I

# Reboot Pi
sudo reboot

# Shutdown Pi
sudo shutdown now
```
