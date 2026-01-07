#!/usr/bin/env python3
"""
Emergency BLE Killer - Use if scanner.py cleanup fails
This will forcefully stop all BLE-related Python processes on macOS
"""

import subprocess
import sys
import time


def kill_ble_processes():
    """Force kill all BLE scanner processes"""
    print("🚨 Emergency BLE Cleanup Starting...")
    print("="*50)

    # Kill scanner.py processes
    print("\n1️⃣  Killing scanner.py processes...")
    try:
        result = subprocess.run(
            ["pkill", "-9", "-f", "scanner.py"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("   ✅ Killed scanner.py processes")
        else:
            print("   ℹ️  No scanner.py processes found")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")

    # Kill bleak-related processes
    print("\n2️⃣  Killing BLE (bleak) processes...")
    try:
        result = subprocess.run(
            ["pkill", "-9", "-f", "bleak"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("   ✅ Killed bleak processes")
        else:
            print("   ℹ️  No bleak processes found")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")

    # Find any Python processes with high CPU
    print("\n3️⃣  Checking for Python processes with high CPU...")
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )

        high_cpu_python = []
        for line in result.stdout.split('\n'):
            if 'python' in line.lower():
                parts = line.split()
                if len(parts) > 2:
                    try:
                        cpu = float(parts[2])
                        if cpu > 5.0:  # More than 5% CPU
                            high_cpu_python.append(line)
                    except ValueError:
                        pass

        if high_cpu_python:
            print("   ⚠️  Found Python processes with high CPU:")
            for proc in high_cpu_python:
                print(f"      {proc}")
            print("\n   💡 You may want to manually kill these PIDs")
        else:
            print("   ✅ No high-CPU Python processes found")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")

    # Restart Bluetooth daemon (requires sudo)
    print("\n4️⃣  Restarting Bluetooth daemon (requires password)...")
    try:
        result = subprocess.run(
            ["sudo", "killall", "-HUP", "blued"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("   ✅ Bluetooth daemon restarted")
            time.sleep(2)
        else:
            print("   ℹ️  Could not restart daemon (may not be needed)")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")

    # Final verification
    print("\n5️⃣  Final verification...")
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )

        ble_processes = [line for line in result.stdout.split('\n')
                         if 'scanner' in line or 'bleak' in line]
        ble_processes = [p for p in ble_processes if 'grep' not in p]

        if ble_processes:
            print("   ⚠️  Still found BLE processes:")
            for proc in ble_processes:
                print(f"      {proc}")
        else:
            print("   ✅ All BLE processes stopped!")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")

    print("\n" + "="*50)
    print("🎉 Emergency cleanup complete!")
    print("\n💡 Next steps:")
    print("   1. Check Activity Monitor → Energy tab")
    print("   2. Toggle Bluetooth OFF/ON in System Preferences")
    print("   3. Restart Mac if battery drain continues")
    print()


if __name__ == "__main__":
    print("\n⚠️  WARNING: This will forcefully kill all BLE scanner processes!")
    print("Only use this if normal Ctrl+C doesn't work.\n")

    try:
        response = input("Continue? [y/N]: ")
        if response.lower() == 'y':
            kill_ble_processes()
        else:
            print("Cancelled.")
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
