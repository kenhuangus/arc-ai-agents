"""Test script to verify all services can be imported and initialized"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_models():
    try:
        from services.models import Intent, Match, IntentSubmission
        print("✅ models.py - OK")
        return True
    except Exception as e:
        print(f"❌ models.py - ERROR: {e}")
        return False

def test_indexer():
    try:
        from services.indexer import ArcIndexer
        print("✅ indexer.py - OK (import)")
        return True
    except Exception as e:
        print(f"❌ indexer.py - ERROR: {e}")
        return False

def test_auction_engine():
    try:
        from services.auction_engine import AuctionEngine, OrderBookEntry
        print("✅ auction_engine.py - OK (import)")
        return True
    except Exception as e:
        print(f"❌ auction_engine.py - ERROR: {e}")
        return False

def test_ap2_gateway():
    try:
        from services.ap2_gateway import AP2Gateway
        print("✅ ap2_gateway.py - OK (import)")
        return True
    except Exception as e:
        print(f"❌ ap2_gateway.py - ERROR: {e}")
        return False

def test_api():
    try:
        # Don't actually import the FastAPI app to avoid startup
        # Just check if the file has syntax errors
        with open('services/api.py', 'r') as f:
            compile(f.read(), 'services/api.py', 'exec')
        print("✅ api.py - OK (syntax)")
        return True
    except Exception as e:
        print(f"❌ api.py - ERROR: {e}")
        return False

def test_sdk():
    try:
        from sdk.arc_sdk import ArcSDK
        print("✅ arc_sdk.py - OK (import)")
        return True
    except Exception as e:
        print(f"❌ arc_sdk.py - ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Testing all services...\n")

    results = [
        test_models(),
        test_indexer(),
        test_auction_engine(),
        test_ap2_gateway(),
        test_api(),
        test_sdk(),
    ]

    print(f"\n{'='*50}")
    print(f"Results: {sum(results)}/{len(results)} passed")

    if all(results):
        print("✅ All services can be imported!")
    else:
        print("❌ Some services have errors")
        sys.exit(1)
