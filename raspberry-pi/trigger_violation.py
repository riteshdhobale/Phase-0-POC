"""
Manual violation trigger script for testing
Use this to simulate safety violations during Phase-0 POC
"""

import requests
import sys

# Backend configuration - CHANGE THIS TO YOUR MACBOOK IP
BACKEND_URL = "http://192.168.31.187:8000"

# Note: This script is for future use when adding safety violation features
# Currently Phase-0 POC focuses on proximity ticketing only


def trigger_violation(coach_id="C1", door_id="D1"):
    """
    Trigger a violation event (for future safety feature implementation).

    Args:
        coach_id: Coach identifier (default: "C1")
        door_id: Door identifier (default: "D1")
    """
    try:
        print(
            f"🚨 Triggering violation for Coach {coach_id}, Door {door_id}...")

        response = requests.post(
            f"{BACKEND_URL}/trigger_violation",
            params={
                "coach_id": coach_id,
                "door_id": door_id
            },
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Violation triggered successfully")
            print(f"   Fine amount: ₹{data.get('fine', 0)}")
            print(f"   Remaining balance: ₹{data.get('remaining_balance', 0)}")
        else:
            print(f"⚠️  Trigger failed: {response.status_code}")
            print(f"   Response: {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")


def check_active_journeys():
    """
    Check how many active journeys exist (for debugging).
    """
    print("📊 Checking active journeys...")
    print("   (This requires backend API extension - coming in Phase-1)")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("⚠️  VIOLATION TRIGGER (Phase-1 Feature)")
    print("="*60)
    print("\nNote: Phase-0 POC focuses on proximity-based ticketing.")
    print("Safety violation features will be added in Phase-1.")
    print("\nCurrently, violations are triggered automatically when")
    print("a user exits the BLE detection range (journey_end).\n")

    # Parse command line arguments
    if len(sys.argv) > 1:
        coach_id = sys.argv[1] if len(sys.argv) > 1 else "C1"
        door_id = sys.argv[2] if len(sys.argv) > 2 else "D1"
        trigger_violation(coach_id, door_id)
    else:
        print("Usage: python3 trigger_violation.py [coach_id] [door_id]")
        print("Example: python3 trigger_violation.py C1 D1")
