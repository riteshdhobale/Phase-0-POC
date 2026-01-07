"""
Raspberry Pi BLE Scanner for Railway POC
Detects Android phone BLE advertisements and manages journey lifecycle
"""

import asyncio
import requests
import time
import signal
import sys
import atexit
from datetime import datetime
from bleak import BleakScanner

# Backend configuration - CHANGE THIS TO YOUR MACBOOK IP
BACKEND_URL = "http://192.168.31.187:8000"

# RSSI threshold for proximity detection (in dBm)
# -70 dBm = close proximity (~2-3 meters, inside train)
# -80 dBm = wider range (~5-6 meters)
RSSI_THRESHOLD = -70

# Exit detection delay (seconds)
# User is considered "exited" only if not detected for this duration
EXIT_DELAY_SECONDS = 10

# Scan interval (seconds)
SCAN_INTERVAL = 2

# Debug mode - set to True to see all detected BLE devices
DEBUG_MODE = True

# Track currently detected users
# Format: {user_id: {'last_seen': timestamp, 'journey_started': bool}}
detected_users = {}

# Global flag for graceful shutdown
shutdown_flag = False

# Store active scanner reference for cleanup
active_scanner = None


def extract_user_id(device):
    """
    Extract user_id from BLE advertisement data.
    Looks for service data containing 'RAIL_USER::<user_id>' payload.
    """
    try:
        # Check service data for our custom UUID (0000fff0-0000-1000-8000-00805f9b34fb)
        if device.metadata and 'service_data' in device.metadata:
            for uuid, data in device.metadata['service_data'].items():
                try:
                    # Debug: print what we're receiving
                    # print(f"DEBUG: Service UUID: {uuid}, Data: {data}")
                    payload = data.decode('utf-8')
                    if payload.startswith('RAIL_USER::'):
                        user_id = payload.replace('RAIL_USER::', '')
                        print(
                            f"✅ Found user in service_data: {user_id[:8]}...")
                        return user_id
                except Exception as e:
                    # print(f"DEBUG: Could not decode service_data: {e}")
                    pass

        # Also check manufacturer data as fallback
        if device.metadata and 'manufacturer_data' in device.metadata:
            for manufacturer_id, data in device.metadata['manufacturer_data'].items():
                try:
                    payload = data.decode('utf-8')
                    if 'RAIL_USER::' in payload:
                        user_id = payload.split('RAIL_USER::')[1]
                        print(
                            f"✅ Found user in manufacturer_data: {user_id[:8]}...")
                        return user_id
                except:
                    pass
    except Exception as e:
        pass

    return None


def start_journey(user_id):
    """
    Call backend to start journey when user is detected.
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/journey_start",
            params={"user_id": user_id},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Journey started for user {user_id[:8]}...")
            print(f"   Journey ID: {data.get('journey_id', 'N/A')[:8]}...")
            return True
        else:
            print(f"⚠️  Journey start failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error starting journey: {e}")
        return False


def end_journey(user_id):
    """
    Call backend to end journey when user exits (fare is deducted).
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/journey_end",
            params={"user_id": user_id},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            print(f"🎫 Journey ended for user {user_id[:8]}...")
            print(f"   Fare deducted: ₹{data.get('fare_amount', 0)}")
            print(f"   Remaining balance: ₹{data.get('remaining_balance', 0)}")
            return True
        else:
            print(f"⚠️  Journey end failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error ending journey: {e}")
        return False


def cleanup_ble():
    """
    Emergency cleanup function to stop all BLE activity.
    Called on exit to ensure no BLE scanning remains active.
    """
    global active_scanner, shutdown_flag

    print("\n🧹 Cleaning up BLE resources...")

    shutdown_flag = True

    # If there's an active scanner, try to stop it
    if active_scanner is not None:
        try:
            print("   ⏹️  Stopping BLE scanner...")
            # BleakScanner cleanup happens automatically when object is destroyed
            active_scanner = None
        except Exception as e:
            print(f"   ⚠️  Error stopping scanner: {e}")

    # End all active journeys gracefully
    if detected_users:
        print(f"   📋 Ending {len(detected_users)} active journey(s)...")
        for user_id, info in list(detected_users.items()):
            if info.get('journey_started', False):
                try:
                    end_journey(user_id)
                except Exception as e:
                    print(
                        f"   ⚠️  Could not end journey for {user_id[:8]}: {e}")
        detected_users.clear()

    print("   ✅ BLE cleanup complete - Mac Bluetooth is now idle")
    print("   💡 You can verify with: system_profiler SPBluetoothDataType | grep Power\n")


def signal_handler(sig, frame):
    """
    Handle termination signals (SIGINT, SIGTERM, SIGQUIT).
    Ensures cleanup runs before exit.
    """
    signal_names = {
        signal.SIGINT: "SIGINT (Ctrl+C)",
        signal.SIGTERM: "SIGTERM",
        signal.SIGQUIT: "SIGQUIT"
    }

    print(
        f"\n\n🛑 Received {signal_names.get(sig, 'signal')} - shutting down gracefully...")

    cleanup_ble()

    print("👋 Scanner stopped. Mac Bluetooth restored to normal state.")
    sys.exit(0)


async def scan_ble_devices():
    """
    Continuously scan for BLE devices and detect railway app users.
    """
    global active_scanner, shutdown_flag

    print(f"🔍 Starting BLE scanner...")
    print(f"📡 RSSI threshold: {RSSI_THRESHOLD} dBm")
    print(f"⏱️  Exit delay: {EXIT_DELAY_SECONDS} seconds")
    print(f"🌐 Backend: {BACKEND_URL}")
    print(f"{'='*60}\n")
    print("📡 Scanning for BLE devices...\n")

    scan_count = 0

    while not shutdown_flag:
        try:
            # Create scanner instance
            active_scanner = BleakScanner()

            # Scan for BLE devices with timeout
            devices = await active_scanner.discover(timeout=SCAN_INTERVAL)

            # Clear scanner reference after scan completes
            active_scanner = None

            current_time = time.time()
            detected_now = set()

            # Debug: show total devices detected
            if DEBUG_MODE and devices:
                print(f"\n🔍 Scan found {len(devices)} BLE device(s)")

            # Process each detected device
            for device in devices:
                # Check shutdown flag
                if shutdown_flag:
                    break

                # Debug: show all devices with good signal
                if DEBUG_MODE and device.rssi >= RSSI_THRESHOLD:
                    print(
                        f"   📱 Device: {device.name or device.address} | RSSI: {device.rssi} dBm")
                    if hasattr(device, 'metadata') and device.metadata:
                        if 'service_data' in device.metadata:
                            print(
                                f"      Service Data UUIDs: {list(device.metadata['service_data'].keys())}")

                # Check RSSI threshold (signal strength)
                if device.rssi < RSSI_THRESHOLD:
                    continue

                # Try to extract user_id from advertisement
                user_id = extract_user_id(device)

                if user_id:
                    detected_now.add(user_id)

                    # New user detected
                    if user_id not in detected_users:
                        print(f"\n🚶 NEW USER DETECTED")
                        print(f"   User ID: {user_id[:8]}...")
                        print(f"   Device: {device.name or 'Unknown'}")
                        print(f"   RSSI: {device.rssi} dBm")
                        print(
                            f"   Time: {datetime.now().strftime('%H:%M:%S')}")

                        detected_users[user_id] = {
                            'last_seen': current_time,
                            'journey_started': False
                        }

                        # Start journey
                        if start_journey(user_id):
                            detected_users[user_id]['journey_started'] = True

                    # User still in range - update last seen
                    else:
                        detected_users[user_id]['last_seen'] = current_time
                        # Optionally print periodic updates
                        # print(f"👤 User {user_id[:8]}... still in range (RSSI: {device.rssi} dBm)")

            # Check for users who have exited (not detected recently)
            users_to_remove = []

            for user_id, info in detected_users.items():
                if shutdown_flag:
                    break

                time_since_last_seen = current_time - info['last_seen']

                # User has been gone for EXIT_DELAY_SECONDS
                if time_since_last_seen > EXIT_DELAY_SECONDS:
                    if info['journey_started']:
                        print(f"\n🚪 USER EXITED")
                        print(f"   User ID: {user_id[:8]}...")
                        print(
                            f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                        print(
                            f"   Out of range for: {int(time_since_last_seen)}s")

                        # End journey (deduct fare)
                        end_journey(user_id)

                    users_to_remove.append(user_id)

            # Remove exited users from tracking
            for user_id in users_to_remove:
                del detected_users[user_id]

            # Show currently tracked users or heartbeat
            scan_count += 1
            if detected_users and not shutdown_flag:
                print(
                    f"📊 Currently tracking {len(detected_users)} user(s)", end='\r')
            elif scan_count % 10 == 0:  # Every 10 scans (~20 seconds)
                print(
                    f"💚 Scanner active - waiting for devices... ({scan_count} scans)", end='\r')

        except Exception as e:
            if not shutdown_flag:
                print(f"❌ Scan error: {e}")
            await asyncio.sleep(1)

        # Small delay before next scan (only if not shutting down)
        if not shutdown_flag:
            await asyncio.sleep(0.5)


def test_backend_connection():
    """
    Test connection to backend before starting scanner.
    """
    print("🔌 Testing backend connection...")
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        if response.status_code == 200:
            print(f"✅ Backend is reachable at {BACKEND_URL}")
            return True
        else:
            print(f"⚠️  Backend returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach backend: {e}")
        print(f"   Make sure MacBook backend is running at {BACKEND_URL}")
        return False


def main():
    """
    Main entry point - test connection and start scanner.
    """
    global shutdown_flag

    print("\n" + "="*60)
    print("🚂 RAILWAY POC - RASPBERRY PI BLE SCANNER")
    print("="*60 + "\n")

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill command
    signal.signal(signal.SIGQUIT, signal_handler)  # Ctrl+\

    # Register cleanup function to run on normal exit
    atexit.register(cleanup_ble)

    print("✅ Cleanup handlers registered (SIGINT, SIGTERM, SIGQUIT, exit)")
    print("   Press Ctrl+C to stop gracefully\n")

    # Test backend connection first
    if not test_backend_connection():
        print("\n⚠️  Please start the backend server first and update BACKEND_URL")
        return

    print("\n✅ Starting BLE proximity detection...\n")

    try:
        # Run async scanner
        asyncio.run(scan_ble_devices())
    except KeyboardInterrupt:
        # Signal handler will take care of cleanup
        pass
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        cleanup_ble()
    finally:
        if not shutdown_flag:
            print("\n\n🛑 Scanner stopped")
            print(f"Final tracked users: {len(detected_users)}")
            cleanup_ble()


if __name__ == "__main__":
    main()
