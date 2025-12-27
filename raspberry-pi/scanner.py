"""
Raspberry Pi BLE Scanner for Railway POC
Detects Android phone BLE advertisements and manages journey lifecycle
"""

import asyncio
import requests
import time
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

# Track currently detected users
# Format: {user_id: {'last_seen': timestamp, 'journey_started': bool}}
detected_users = {}


def extract_user_id(device):
    """
    Extract user_id from BLE advertisement data.
    Looks for service data containing 'RAIL_USER::<user_id>' payload.
    """
    try:
        # Check service data for our custom UUID
        if device.metadata and 'service_data' in device.metadata:
            for uuid, data in device.metadata['service_data'].items():
                try:
                    payload = data.decode('utf-8')
                    if payload.startswith('RAIL_USER::'):
                        user_id = payload.replace('RAIL_USER::', '')
                        return user_id
                except:
                    pass

        # Also check manufacturer data as fallback
        if device.metadata and 'manufacturer_data' in device.metadata:
            for manufacturer_id, data in device.metadata['manufacturer_data'].items():
                try:
                    payload = data.decode('utf-8')
                    if 'RAIL_USER::' in payload:
                        user_id = payload.split('RAIL_USER::')[1]
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


async def scan_ble_devices():
    """
    Continuously scan for BLE devices and detect railway app users.
    """
    print(f"🔍 Starting BLE scanner...")
    print(f"📡 RSSI threshold: {RSSI_THRESHOLD} dBm")
    print(f"⏱️  Exit delay: {EXIT_DELAY_SECONDS} seconds")
    print(f"🌐 Backend: {BACKEND_URL}")
    print(f"{'='*60}\n")

    while True:
        try:
            # Scan for BLE devices
            devices = await BleakScanner.discover(timeout=SCAN_INTERVAL)

            current_time = time.time()
            detected_now = set()

            # Process each detected device
            for device in devices:
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

            # Show currently tracked users
            if detected_users:
                print(
                    f"\n📊 Currently tracking {len(detected_users)} user(s)", end='\r')

        except Exception as e:
            print(f"❌ Scan error: {e}")
            await asyncio.sleep(1)

        # Small delay before next scan
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
    print("\n" + "="*60)
    print("🚂 RAILWAY POC - RASPBERRY PI BLE SCANNER")
    print("="*60 + "\n")

    # Test backend connection first
    if not test_backend_connection():
        print("\n⚠️  Please start the backend server first and update BACKEND_URL")
        return

    print("\n✅ Starting BLE proximity detection...\n")

    try:
        # Run async scanner
        asyncio.run(scan_ble_devices())
    except KeyboardInterrupt:
        print("\n\n🛑 Scanner stopped by user")
        print(f"Final tracked users: {len(detected_users)}")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")


if __name__ == "__main__":
    main()
