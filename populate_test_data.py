#!/usr/bin/env python3
"""
Populate Arc Coordination System with test data
Creates intents, matches, and mandates for dashboard visualization
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from web3 import Web3
from eth_account import Account
import json
import hashlib

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.indexer import ArcIndexer, IntentDB, MatchDB
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv("config/.env")

# Configuration
RPC_URL = os.getenv("ARC_TESTNET_RPC_URL", "http://localhost:8545")
INTENT_REGISTRY = os.getenv("INTENT_REGISTRY_ADDRESS")
AUCTION_ESCROW = os.getenv("AUCTION_ESCROW_ADDRESS")
PAYMENT_ROUTER = os.getenv("PAYMENT_ROUTER_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
DB_URL = "sqlite:///data/arc_intents.db"

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = Account.from_key(PRIVATE_KEY)

print(f"Using account: {account.address}")
print(f"Balance: {w3.eth.get_balance(account.address) / 10**18} ETH")


def get_intent_registry_abi():
    """Get IntentRegistry contract ABI"""
    return [
        {
            "inputs": [
                {"name": "_intentHash", "type": "bytes32"},
                {"name": "_validUntil", "type": "uint256"},
                {"name": "_ap2MandateId", "type": "bytes32"},
                {"name": "_settlementAsset", "type": "string"}
            ],
            "name": "registerIntent",
            "outputs": [{"name": "intentId", "type": "bytes32"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "intentId", "type": "bytes32"},
                {"indexed": True, "name": "actor", "type": "address"},
                {"indexed": False, "name": "intentHash", "type": "bytes32"},
                {"indexed": False, "name": "timestamp", "type": "uint256"}
            ],
            "name": "IntentRegistered",
            "type": "event"
        }
    ]


def create_test_intent(intent_type, price, quantity, asset, description):
    """Create a test intent and submit to blockchain"""
    print(f"\n📝 Creating {intent_type} intent: {description}")

    # Create intent payload
    payload = {
        "type": intent_type,
        "price": price,
        "quantity": quantity,
        "asset": asset,
        "description": description,
        "timestamp": int(datetime.now().timestamp())
    }

    # Hash the payload
    payload_json = json.dumps(payload, sort_keys=True)
    intent_hash = hashlib.sha256(payload_json.encode()).hexdigest()

    # Generate mandate ID
    mandate_id = hashlib.sha256(f"mandate_{intent_type}_{price}".encode()).hexdigest()

    # Calculate valid_until (7 days from now)
    valid_until = int((datetime.now() + timedelta(days=7)).timestamp())

    try:
        # Get contract
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(INTENT_REGISTRY),
            abi=get_intent_registry_abi()
        )

        # Build transaction
        tx = contract.functions.registerIntent(
            bytes.fromhex(intent_hash),
            valid_until,
            bytes.fromhex(mandate_id),
            asset
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price
        })

        # Sign and send
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        print(f"  ⏳ Transaction sent: {tx_hash.hex()}")

        # Wait for receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)

        if receipt['status'] == 1:
            # Parse the IntentRegistered event
            intent_id = receipt['logs'][0]['topics'][1].hex() if receipt['logs'] else None
            print(f"  ✅ Intent created: {intent_id}")

            # Store in database
            engine = create_engine(DB_URL)
            Session = sessionmaker(bind=engine)
            session = Session()

            intent_db = IntentDB(
                intent_id=intent_id or f"0x{intent_hash}",
                intent_hash=f"0x{intent_hash}",
                actor=account.address,
                timestamp=int(datetime.now().timestamp()),
                valid_until=valid_until,
                ap2_mandate_id=f"0x{mandate_id}",
                settlement_asset=asset,
                is_active=True,
                is_matched=False
            )

            session.add(intent_db)
            session.commit()
            session.close()

            return intent_id, intent_hash
        else:
            print(f"  ❌ Transaction failed")
            return None, None

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None, None


def populate_database():
    """Populate database with test intents"""
    print("\n" + "="*60)
    print("🚀 Arc Coordination System - Test Data Population")
    print("="*60)

    # Create database directory
    os.makedirs("data", exist_ok=True)

    # Initialize database
    engine = create_engine(DB_URL)
    IntentDB.metadata.create_all(engine)
    MatchDB.metadata.create_all(engine)

    print("\n✅ Database initialized")

    # Test data scenarios
    test_intents = [
        # Active Bids
        ("bid", 10000, 1, "USD", "Buy 1 BTC at $10,000"),
        ("bid", 9800, 2, "USD", "Buy 2 BTC at $9,800"),
        ("bid", 3200, 5, "USD", "Buy 5 ETH at $3,200"),
        ("bid", 9900, 1, "USD", "Buy 1 BTC at $9,900"),

        # Active Asks
        ("ask", 10200, 1, "USD", "Sell 1 BTC at $10,200"),
        ("ask", 10500, 2, "USD", "Sell 2 BTC at $10,500"),
        ("ask", 3300, 5, "USD", "Sell 5 ETH at $3,300"),
        ("ask", 10100, 1, "USD", "Sell 1 BTC at $10,100"),

        # Mixed assets
        ("bid", 30, 100, "USDC", "Buy 100 USDC worth of stablecoins"),
        ("ask", 31, 100, "USDC", "Sell 100 USDC worth of tokens"),
    ]

    created_intents = []

    for intent_type, price, quantity, asset, description in test_intents:
        intent_id, intent_hash = create_test_intent(
            intent_type, price, quantity, asset, description
        )
        if intent_id:
            created_intents.append({
                "intent_id": intent_id,
                "intent_hash": intent_hash,
                "type": intent_type,
                "price": price,
                "asset": asset,
                "description": description
            })

        # Small delay to avoid nonce issues
        import time
        time.sleep(0.5)

    print("\n" + "="*60)
    print(f"✅ Created {len(created_intents)} test intents")
    print("="*60)

    # Print summary
    print("\n📊 Intent Summary:")
    bids = [i for i in created_intents if i['type'] == 'bid']
    asks = [i for i in created_intents if i['type'] == 'ask']
    print(f"  💰 Bids: {len(bids)}")
    print(f"  💵 Asks: {len(asks)}")
    print(f"  📈 Total: {len(created_intents)}")

    # Show order book
    print("\n📖 Order Book Preview:")
    print("\n  BID SIDE:")
    for bid in sorted(bids, key=lambda x: x['price'], reverse=True)[:5]:
        print(f"    ${bid['price']:,} - {bid['description']}")

    print("\n  ASK SIDE:")
    for ask in sorted(asks, key=lambda x: x['price'])[:5]:
        print(f"    ${ask['price']:,} - {ask['description']}")

    print("\n✨ Test data population complete!")
    print(f"🌐 View dashboard at: http://localhost:8502")
    print(f"🔌 API available at: http://localhost:8000")
    print(f"📚 Check intents: http://localhost:8000/intents")


if __name__ == "__main__":
    populate_database()
