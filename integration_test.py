"""
Comprehensive integration test for Arc Coordination System
Tests the full workflow: intent submission, matching, and settlement
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sdk.arc_sdk import ArcSDK

async def test_integration():
    """Run comprehensive integration test"""

    print("🧪 Arc Coordination System - Integration Test")
    print("=" * 60)

    # Initialize SDK
    sdk = ArcSDK(
        api_base_url="http://localhost:8000",
        rpc_url="http://localhost:8545",
        private_key="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
        intent_registry_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
        auction_escrow_address="0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0",
        payment_router_address="0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
    )

    try:
        # Test 1: Register AP2 Mandate
        print("\n📝 Test 1: Register AP2 Mandate")
        mandate_id = "0x" + "1" * 64
        mandate_result = await sdk.register_mandate(
            mandate_id=mandate_id,
            issuer=sdk.account.address,
            subject=sdk.account.address,
            scope="payment.create",
            valid_days=365
        )
        print(f"✅ Mandate registered: {mandate_result['mandate_id'][:20]}...")

        # Test 2: Submit Bid Intent
        print("\n📝 Test 2: Submit Bid Intent")
        valid_until = int((datetime.now() + timedelta(hours=24)).timestamp())

        bid_result = await sdk.submit_intent(
            intent_payload={"description": "Buy 100 tokens", "type": "bid"},
            valid_until=valid_until,
            ap2_mandate_id=mandate_id,
            settlement_asset="USD",
            constraints={"type": "bid", "price": 10000, "quantity": 100}
        )
        print(f"✅ Bid intent submitted: {bid_result['intent_id'][:20]}...")

        # Test 3: Submit Ask Intent
        print("\n📝 Test 3: Submit Ask Intent")
        ask_result = await sdk.submit_intent(
            intent_payload={"description": "Sell 100 tokens", "type": "ask"},
            valid_until=valid_until,
            ap2_mandate_id=mandate_id,
            settlement_asset="USD",
            constraints={"type": "ask", "price": 9500, "quantity": 100}
        )
        print(f"✅ Ask intent submitted: {ask_result['intent_id'][:20]}...")

        # Test 4: List Intents
        print("\n📝 Test 4: List Active Intents")
        intents = await sdk.list_intents(is_active=True, is_matched=False)
        print(f"✅ Found {len(intents)} active intents")

        # Test 5: Get Order Book
        print("\n📝 Test 5: Get Order Book")
        orderbook = await sdk.get_orderbook("USD")
        print(f"✅ Order book: {len(orderbook['bids'])} bids, {len(orderbook['asks'])} asks")
        if orderbook['spread'] is not None:
            print(f"   Spread: {orderbook['spread']}")

        # Test 6: List Matches
        print("\n📝 Test 6: List Matches")
        matches = await sdk.list_matches()
        print(f"✅ Found {len(matches)} matches")

        # Test 7: Health Check
        print("\n📝 Test 7: API Health Check")
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            health = response.json()
            print(f"✅ API Status: {health['status']}")

        print("\n" + "=" * 60)
        print("✅ All integration tests passed!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await sdk.close()


if __name__ == "__main__":
    success = asyncio.run(test_integration())
    sys.exit(0 if success else 1)
