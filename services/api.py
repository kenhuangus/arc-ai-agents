"""
FastAPI REST API for Arc Coordination System
Provides endpoints for intent submission, querying, matching, and settlement
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
from web3 import Web3
from eth_account import Account
from loguru import logger
from dotenv import load_dotenv

from services.models import (
    Intent, Match, IntentSubmission, MatchRequest,
    MatchStatus, PaymentVerification
)
from services.indexer import ArcIndexer
from services.auction_engine import AuctionEngine, OrderBookEntry, IntentType
from services.ap2_gateway import AP2Gateway

load_dotenv("config/.env")

# Initialize FastAPI app
app = FastAPI(
    title="Arc Coordination System API",
    description="REST API for decentralized intent coordination on Arc L1",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (initialized on startup)
indexer: Optional[ArcIndexer] = None
auction_engine: Optional[AuctionEngine] = None
ap2_gateway: Optional[AP2Gateway] = None
w3: Optional[Web3] = None
account: Optional[Account] = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global indexer, auction_engine, ap2_gateway, w3, account

    rpc_url = os.getenv("ARC_TESTNET_RPC_URL", "http://localhost:8545")
    intent_registry = os.getenv("INTENT_REGISTRY_ADDRESS")
    auction_escrow = os.getenv("AUCTION_ESCROW_ADDRESS")
    payment_router = os.getenv("PAYMENT_ROUTER_ADDRESS")
    private_key = os.getenv("PRIVATE_KEY")
    stripe_key = os.getenv("STRIPE_API_KEY")

    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    account = Account.from_key(private_key)

    # Initialize indexer
    indexer = ArcIndexer(rpc_url, intent_registry, auction_escrow)

    # Initialize auction engine
    auction_engine = AuctionEngine(rpc_url, auction_escrow, private_key, indexer)

    # Initialize AP2 gateway
    ap2_gateway = AP2Gateway(stripe_key, rpc_url, payment_router, private_key)

    logger.info("API services initialized")


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Intent endpoints
@app.post("/intents/submit", response_model=dict)
async def submit_intent(submission: IntentSubmission, background_tasks: BackgroundTasks):
    """
    Submit a new intent to the coordination system

    Args:
        submission: Intent submission data

    Returns:
        Intent ID and transaction hash
    """
    try:
        # Hash the intent payload
        import json
        import hashlib
        payload_json = json.dumps(submission.intent_payload, sort_keys=True)
        intent_hash = hashlib.sha256(payload_json.encode()).hexdigest()

        # Register intent on-chain via IntentRegistry
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(os.getenv("INTENT_REGISTRY_ADDRESS")),
            abi=_get_intent_registry_abi()
        )

        tx = contract.functions.registerIntent(
            bytes.fromhex(intent_hash.replace('0x', '')),
            submission.valid_until,
            bytes.fromhex(submission.ap2_mandate_id.replace('0x', '')),
            submission.settlement_asset
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price
        })

        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        logger.info(f"Intent submitted. Tx: {tx_hash.hex()}")

        # Wait for receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        if receipt['status'] != 1:
            raise HTTPException(status_code=500, detail="Transaction failed")

        # Extract intent ID from logs
        intent_id = None
        try:
            # The IntentRegistered event has the intentId as the first indexed parameter
            if receipt['logs'] and len(receipt['logs']) > 0:
                log = receipt['logs'][0]
                if 'topics' in log and len(log['topics']) > 1:
                    # First topic is event signature, second is intentId
                    intent_id = log['topics'][1].hex()
        except (IndexError, KeyError) as e:
            logger.warning(f"Could not extract intent ID from logs: {e}")

        # If we couldn't extract from logs, generate from hash
        if not intent_id:
            intent_id = "0x" + intent_hash
            logger.info(f"Using intent hash as ID: {intent_id}")

        # Store in database via indexer
        from services.indexer import IntentDB
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        try:
            engine = create_engine("sqlite:///arc_coordination.db")
            Session = sessionmaker(bind=engine)
            session = Session()

            intent_db = IntentDB(
                intent_id=intent_id,
                intent_hash="0x" + intent_hash,
                actor=account.address,
                timestamp=int(w3.eth.get_block('latest')['timestamp']),
                valid_until=submission.valid_until,
                ap2_mandate_id=submission.ap2_mandate_id,
                settlement_asset=submission.settlement_asset,
                is_active=True,
                is_matched=False,
                payload=payload_json
            )

            session.add(intent_db)
            session.commit()
            session.close()
            logger.info(f"Intent {intent_id} stored in database")
        except Exception as db_error:
            logger.warning(f"Could not store in database: {db_error}")

        # Trigger indexer update in background
        background_tasks.add_task(indexer.index_events)

        return {
            "intent_id": intent_id,
            "tx_hash": tx_hash.hex(),
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error submitting intent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/intents", response_model=List[dict])
async def list_intents(
    actor: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_matched: Optional[bool] = None
):
    """
    List intents with optional filters

    Args:
        actor: Filter by actor address
        is_active: Filter by active status
        is_matched: Filter by matched status

    Returns:
        List of intents
    """
    intents = indexer.query_intents(actor=actor, is_active=is_active, is_matched=is_matched)

    return [
        {
            "intent_id": i.intent_id,
            "intent_hash": i.intent_hash,
            "actor": i.actor,
            "timestamp": i.timestamp,
            "valid_until": i.valid_until,
            "settlement_asset": i.settlement_asset,
            "is_active": i.is_active,
            "is_matched": i.is_matched
        }
        for i in intents
    ]


@app.get("/intents/{intent_id}", response_model=dict)
async def get_intent(intent_id: str):
    """Get specific intent by ID"""
    intents = indexer.query_intents()
    intent = next((i for i in intents if i.intent_id == intent_id), None)

    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")

    return {
        "intent_id": intent.intent_id,
        "intent_hash": intent.intent_hash,
        "actor": intent.actor,
        "timestamp": intent.timestamp,
        "valid_until": intent.valid_until,
        "settlement_asset": intent.settlement_asset,
        "is_active": intent.is_active,
        "is_matched": intent.is_matched
    }


@app.post("/intents/{intent_id}/cancel")
async def cancel_intent(intent_id: str):
    """Cancel an active intent"""
    try:
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(os.getenv("INTENT_REGISTRY_ADDRESS")),
            abi=_get_intent_registry_abi()
        )

        tx = contract.functions.cancelIntent(
            bytes.fromhex(intent_id.replace('0x', ''))
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 200000,
            'gasPrice': w3.eth.gas_price
        })

        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        if receipt['status'] != 1:
            raise HTTPException(status_code=500, detail="Transaction failed")

        return {"status": "cancelled", "tx_hash": tx_hash.hex()}

    except Exception as e:
        logger.error(f"Error cancelling intent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Match endpoints
@app.get("/matches", response_model=List[dict])
async def list_matches(
    status: Optional[str] = None,
    bidder: Optional[str] = None,
    asker: Optional[str] = None
):
    """List matches with optional filters"""
    matches = indexer.query_matches(status=status, bidder=bidder, asker=asker)

    return [
        {
            "match_id": m.match_id,
            "bid_intent_id": m.bid_intent_id,
            "ask_intent_id": m.ask_intent_id,
            "bidder": m.bidder,
            "asker": m.asker,
            "match_price": m.match_price,
            "created_at": m.created_at,
            "settle_by": m.settle_by,
            "status": m.status
        }
        for m in matches
    ]


@app.get("/matches/{match_id}", response_model=dict)
async def get_match(match_id: str):
    """Get specific match by ID"""
    matches = indexer.query_matches()
    match = next((m for m in matches if m.match_id == match_id), None)

    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    return {
        "match_id": match.match_id,
        "bid_intent_id": match.bid_intent_id,
        "ask_intent_id": match.ask_intent_id,
        "bidder": match.bidder,
        "asker": match.asker,
        "match_price": match.match_price,
        "created_at": match.created_at,
        "settle_by": match.settle_by,
        "status": match.status
    }


# Order book endpoint
@app.get("/orderbook/{asset}", response_model=dict)
async def get_orderbook(asset: str):
    """Get current order book for an asset"""
    return auction_engine.get_order_book_snapshot(asset)


# Payment endpoints
@app.post("/payments/create-intent", response_model=dict)
async def create_payment_intent(
    amount: int,
    currency: str,
    payer: str,
    payee: str,
    mandate_id: str
):
    """Create a Stripe payment intent for AP2 settlement"""
    result = await ap2_gateway.create_payment_intent(
        amount, currency, payer, payee, mandate_id
    )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to create payment intent")

    return result


@app.post("/payments/verify", response_model=dict)
async def verify_payment(payment_intent_id: str):
    """Verify a Stripe payment and anchor on-chain"""
    verification = await ap2_gateway.verify_payment(payment_intent_id)

    if not verification:
        raise HTTPException(status_code=404, detail="Payment not verified")

    # Anchor on-chain
    tx_hash = await ap2_gateway.anchor_payment_onchain(
        payment_intent_id,
        verification["amount"],
        verification["payer"],
        verification["payee"],
        verification["mandate_id"]
    )

    return {**verification, "tx_hash": tx_hash}


# Mandate endpoints
@app.post("/mandates/register", response_model=dict)
async def register_mandate(
    mandate_id: str,
    issuer: str,
    subject: str,
    scope: str,
    valid_days: int = 365
):
    """Register an AP2 payment mandate"""
    from datetime import timedelta

    mandate = ap2_gateway.register_mandate(
        mandate_id,
        issuer,
        subject,
        scope,
        datetime.now() + timedelta(days=valid_days)
    )

    return mandate


def _get_intent_registry_abi():
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
            "inputs": [{"name": "_intentId", "type": "bytes32"}],
            "name": "cancelIntent",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))

    uvicorn.run(app, host=host, port=port)
