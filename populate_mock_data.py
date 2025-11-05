#!/usr/bin/env python3
"""
Populate Arc Coordination System with mock test data
Creates sample intents and matches directly in the database
"""
import sys
import os
from datetime import datetime, timedelta
import hashlib
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.indexer import IntentDB, MatchDB, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use the same database as the API
DB_URL = "sqlite:///arc_coordination.db"

# Test account address (from Anvil)
TEST_ACCOUNT = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
TEST_ACCOUNT_2 = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
TEST_ACCOUNT_3 = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"

def generate_id(prefix: str) -> str:
    """Generate a random hex ID"""
    random_bytes = os.urandom(32)
    return "0x" + random_bytes.hex()

def generate_hash(data: str) -> str:
    """Generate SHA256 hash"""
    return "0x" + hashlib.sha256(data.encode()).hexdigest()

def create_mock_intents(session):
    """Create mock intents in database"""
    print("\n📝 Creating mock intents...")

    now = int(datetime.now().timestamp())
    one_week = int((datetime.now() + timedelta(days=7)).timestamp())

    test_intents = [
        # Active Bids (buy orders)
        {
            "type": "bid",
            "price": 10000,
            "quantity": 1,
            "asset": "USD",
            "description": "Buy 1 BTC at $10,000",
            "actor": TEST_ACCOUNT
        },
        {
            "type": "bid",
            "price": 9800,
            "quantity": 2,
            "asset": "USD",
            "description": "Buy 2 BTC at $9,800",
            "actor": TEST_ACCOUNT
        },
        {
            "type": "bid",
            "price": 3200,
            "quantity": 5,
            "asset": "USD",
            "description": "Buy 5 ETH at $3,200",
            "actor": TEST_ACCOUNT_2
        },
        {
            "type": "bid",
            "price": 9900,
            "quantity": 1,
            "asset": "USD",
            "description": "Buy 1 BTC at $9,900",
            "actor": TEST_ACCOUNT_3
        },
        {
            "type": "bid",
            "price": 30,
            "quantity": 100,
            "asset": "USDC",
            "description": "Buy 100 USDC",
            "actor": TEST_ACCOUNT
        },

        # Active Asks (sell orders)
        {
            "type": "ask",
            "price": 10200,
            "quantity": 1,
            "asset": "USD",
            "description": "Sell 1 BTC at $10,200",
            "actor": TEST_ACCOUNT_2
        },
        {
            "type": "ask",
            "price": 10500,
            "quantity": 2,
            "asset": "USD",
            "description": "Sell 2 BTC at $10,500",
            "actor": TEST_ACCOUNT
        },
        {
            "type": "ask",
            "price": 3300,
            "quantity": 5,
            "asset": "USD",
            "description": "Sell 5 ETH at $3,300",
            "actor": TEST_ACCOUNT_3
        },
        {
            "type": "ask",
            "price": 10100,
            "quantity": 1,
            "asset": "USD",
            "description": "Sell 1 BTC at $10,100",
            "actor": TEST_ACCOUNT_2
        },
        {
            "type": "ask",
            "price": 31,
            "quantity": 100,
            "asset": "USDC",
            "description": "Sell 100 USDC",
            "actor": TEST_ACCOUNT_3
        },
    ]

    created_intents = []

    for intent_data in test_intents:
        intent_id = generate_id("intent")
        intent_hash = generate_hash(f"{intent_data['type']}_{intent_data['price']}_{intent_data['quantity']}")
        mandate_id = generate_id("mandate")

        intent = IntentDB(
            intent_id=intent_id,
            intent_hash=intent_hash,
            actor=intent_data['actor'],
            timestamp=now - random.randint(0, 3600),  # Random time in last hour
            valid_until=one_week,
            ap2_mandate_id=mandate_id,
            settlement_asset=intent_data['asset'],
            is_active=True,
            is_matched=False,
            payload=None
        )

        session.add(intent)
        created_intents.append({
            "intent_id": intent_id,
            "type": intent_data['type'],
            "price": intent_data['price'],
            "description": intent_data['description'],
            "actor": intent_data['actor']
        })
        print(f"  ✅ Created {intent_data['type']} intent: {intent_data['description']}")

    session.commit()
    return created_intents


def create_mock_matches(session, intents):
    """Create some mock matches"""
    print("\n🔄 Creating mock matches...")

    now = int(datetime.now().timestamp())
    one_day = int((datetime.now() + timedelta(days=1)).timestamp())

    # Create a few matches with different statuses
    bids = [i for i in intents if i['type'] == 'bid']
    asks = [i for i in intents if i['type'] == 'ask']

    match_scenarios = [
        {
            "bid_idx": 0,
            "ask_idx": 0,
            "status": "pending",
            "description": "Pending match - waiting for funding"
        },
        {
            "bid_idx": 1,
            "ask_idx": 1,
            "status": "funded",
            "description": "Funded match - ready for settlement"
        },
        {
            "bid_idx": 2,
            "ask_idx": 2,
            "status": "settled",
            "description": "Settled match - completed"
        },
        {
            "bid_idx": 3,
            "ask_idx": 3,
            "status": "cancelled",
            "description": "Cancelled match"
        },
    ]

    created_matches = []

    for scenario in match_scenarios:
        if scenario['bid_idx'] < len(bids) and scenario['ask_idx'] < len(asks):
            bid = bids[scenario['bid_idx']]
            ask = asks[scenario['ask_idx']]

            match_id = generate_id("match")
            match_price = (bid['price'] + ask['price']) // 2

            match = MatchDB(
                match_id=match_id,
                bid_intent_id=bid['intent_id'],
                ask_intent_id=ask['intent_id'],
                bidder=bid['actor'],
                asker=ask['actor'],
                match_price=match_price,
                created_at=now - random.randint(0, 7200),  # Random time in last 2 hours
                settle_by=one_day,
                status=scenario['status'],
                ap2_proof_hash=generate_hash(f"proof_{match_id}") if scenario['status'] == 'settled' else None
            )

            session.add(match)
            created_matches.append(match)
            print(f"  ✅ Created {scenario['status']} match: ${match_price:,}")

    session.commit()
    return created_matches


def populate_database():
    """Main function to populate database"""
    print("\n" + "="*60)
    print("🚀 Arc Coordination System - Mock Data Population")
    print("="*60)

    # Initialize database
    engine = create_engine(DB_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Clear existing test data (optional)
    print("\n🗑️  Clearing existing data...")
    session.query(MatchDB).delete()
    session.query(IntentDB).delete()
    session.commit()
    print("  ✅ Database cleared")

    # Create test data
    intents = create_mock_intents(session)
    matches = create_mock_matches(session, intents)

    session.close()

    # Print summary
    print("\n" + "="*60)
    print(f"✅ Mock data population complete!")
    print("="*60)

    bids = [i for i in intents if i['type'] == 'bid']
    asks = [i for i in intents if i['type'] == 'ask']

    print(f"\n📊 Summary:")
    print(f"  💰 Bid Intents: {len(bids)}")
    print(f"  💵 Ask Intents: {len(asks)}")
    print(f"  📈 Total Intents: {len(intents)}")
    print(f"  🔄 Matches: {len(matches)}")

    print(f"\n📖 Order Book Preview:")
    print(f"\n  BID SIDE (highest first):")
    for bid in sorted(bids, key=lambda x: x['price'], reverse=True)[:5]:
        print(f"    ${bid['price']:,} - {bid['description']}")

    print(f"\n  ASK SIDE (lowest first):")
    for ask in sorted(asks, key=lambda x: x['price'])[:5]:
        print(f"    ${ask['price']:,} - {ask['description']}")

    print(f"\n🔄 Matches Created:")
    for match in matches:
        print(f"    {match.status.upper()}: ${match.match_price:,}")

    print(f"\n🌐 Access Points:")
    print(f"  Streamlit UI:  http://localhost:8502")
    print(f"  REST API:      http://localhost:8000")
    print(f"  View Intents:  http://localhost:8000/intents")
    print(f"  View Matches:  http://localhost:8000/matches")

    print(f"\n✨ Dashboard should now show data!")


if __name__ == "__main__":
    populate_database()
