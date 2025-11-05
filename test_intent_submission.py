#!/usr/bin/env python3
"""
Test intent submission through the API
"""
import requests
import json
from datetime import datetime, timedelta

API_URL = "http://localhost:8000"

def test_submit_intent():
    """Test submitting a new intent"""
    print("\n🧪 Testing Intent Submission...")
    print("=" * 60)

    # Prepare intent data
    valid_until = int((datetime.now() + timedelta(days=7)).timestamp())

    intent_data = {
        "intent_payload": {
            "type": "bid",
            "price": 11000,
            "quantity": 1,
            "asset": "BTC",
            "description": "Test buy 1 BTC at $11,000"
        },
        "valid_until": valid_until,
        "ap2_mandate_id": "0x" + "11" * 32,  # Test mandate ID
        "settlement_asset": "USD"
    }

    print(f"\n📝 Submitting Intent:")
    print(f"   Type: {intent_data['intent_payload']['type']}")
    print(f"   Price: ${intent_data['intent_payload']['price']:,}")
    print(f"   Asset: {intent_data['settlement_asset']}")
    print(f"   Description: {intent_data['intent_payload']['description']}")

    try:
        # Submit intent
        response = requests.post(
            f"{API_URL}/intents/submit",
            json=intent_data,
            timeout=30
        )

        print(f"\n📡 Response Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS! Intent submitted:")
            print(f"   Intent ID: {result['intent_id']}")
            print(f"   Tx Hash:   {result['tx_hash']}")
            print(f"   Status:    {result['status']}")

            # Verify intent appears in list
            print(f"\n🔍 Verifying intent in database...")
            list_response = requests.get(f"{API_URL}/intents")
            if list_response.status_code == 200:
                intents = list_response.json()
                new_intent = next((i for i in intents if i['intent_id'] == result['intent_id']), None)
                if new_intent:
                    print(f"   ✅ Intent found in database!")
                    print(f"   Actor: {new_intent['actor']}")
                    print(f"   Active: {new_intent['is_active']}")
                else:
                    print(f"   ⚠️  Intent not yet indexed")

            return True

        else:
            print(f"\n❌ FAILED with status {response.status_code}")
            print(f"   Error: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"\n❌ REQUEST ERROR: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def test_api_health():
    """Test API health"""
    print("\n🏥 Checking API Health...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API Status: {data['status']}")
            return True
        else:
            print(f"   ❌ API unhealthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot reach API: {e}")
        return False


def main():
    """Run tests"""
    print("\n" + "=" * 60)
    print("  Arc Coordination System - Intent Submission Test")
    print("=" * 60)

    # Check API health first
    if not test_api_health():
        print("\n❌ API is not responding. Please start the API first.")
        return

    # Test intent submission
    success = test_submit_intent()

    print("\n" + "=" * 60)
    if success:
        print("  ✅ ALL TESTS PASSED!")
    else:
        print("  ❌ TESTS FAILED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
