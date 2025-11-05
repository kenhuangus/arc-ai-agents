"""Simple API test - start API and test health endpoint"""
import asyncio
import httpx
import uvicorn
import threading
import time
import sys
import os

# Add to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def start_api():
    """Start API server in background thread"""
    from services.api import app
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="error")
    server = uvicorn.Server(config)
    server.run()

async def test_health():
    """Test the health endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                print(f"✅ Health check passed: {response.json()}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

async def test_endpoints():
    """Test various API endpoints"""
    try:
        async with httpx.AsyncClient() as client:
            # Test intents list
            response = await client.get("http://localhost:8000/intents")
            print(f"✅ GET /intents: {response.status_code} - {len(response.json())} intents")

            # Test matches list
            response = await client.get("http://localhost:8000/matches")
            print(f"✅ GET /matches: {response.status_code} - {len(response.json())} matches")

        return True
    except Exception as e:
        print(f"❌ Endpoint test error: {e}")
        return False

if __name__ == "__main__":
    print("Starting API test...\n")

    # Start API in background thread
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()

    # Wait for API to start
    print("Waiting for API to start...")
    time.sleep(5)

    # Run tests
    health_ok = asyncio.run(test_health())

    if health_ok:
        asyncio.run(test_endpoints())
        print("\n✅ API tests passed!")
    else:
        print("\n❌ API tests failed!")
        sys.exit(1)
