"""
Intent Indexer Service - Listens to Arc blockchain events and indexes intents
"""
import asyncio
import json
from typing import Dict, List, Optional
from web3 import Web3
from web3.contract import Contract
from loguru import logger
from sqlalchemy import create_engine, Column, String, Integer, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv("config/.env")

Base = declarative_base()


class IntentDB(Base):
    """Database model for intents"""
    __tablename__ = "intents"

    intent_id = Column(String, primary_key=True)
    intent_hash = Column(String)
    actor = Column(String)
    timestamp = Column(Integer)
    valid_until = Column(Integer)
    ap2_mandate_id = Column(String)
    settlement_asset = Column(String)
    is_active = Column(Boolean, default=True)
    is_matched = Column(Boolean, default=False)
    payload = Column(Text)  # JSON string of off-chain data


class MatchDB(Base):
    """Database model for matches"""
    __tablename__ = "matches"

    match_id = Column(String, primary_key=True)
    bid_intent_id = Column(String)
    ask_intent_id = Column(String)
    bidder = Column(String)
    asker = Column(String)
    match_price = Column(Integer)
    created_at = Column(Integer)
    settle_by = Column(Integer)
    status = Column(String)
    ap2_proof_hash = Column(String, nullable=True)


class ArcIndexer:
    """
    Arc blockchain event indexer for Intent Registry and Auction Escrow
    """

    def __init__(
        self,
        rpc_url: str,
        intent_registry_address: str,
        auction_escrow_address: str,
        db_url: str = "sqlite:///arc_coordination.db"
    ):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.intent_registry_address = intent_registry_address
        self.auction_escrow_address = auction_escrow_address

        # Setup database
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # Load contract ABIs (simplified for demo)
        self.intent_registry_contract = self._load_contract(
            intent_registry_address,
            self._get_intent_registry_abi()
        )
        self.auction_escrow_contract = self._load_contract(
            auction_escrow_address,
            self._get_auction_escrow_abi()
        )

        self.latest_block = 0
        logger.info(f"Indexer initialized. Connected to {rpc_url}")

    def _load_contract(self, address: str, abi: List[dict]) -> Contract:
        """Load contract from address and ABI"""
        checksum_address = Web3.to_checksum_address(address)
        return self.w3.eth.contract(address=checksum_address, abi=abi)

    def _get_intent_registry_abi(self) -> List[dict]:
        """Get IntentRegistry contract ABI"""
        # Simplified ABI with event signatures
        return [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "intentId", "type": "bytes32"},
                    {"indexed": True, "name": "intentHash", "type": "bytes32"},
                    {"indexed": True, "name": "actor", "type": "address"},
                    {"indexed": False, "name": "timestamp", "type": "uint256"},
                    {"indexed": False, "name": "validUntil", "type": "uint256"},
                    {"indexed": False, "name": "ap2MandateId", "type": "bytes32"},
                    {"indexed": False, "name": "settlementAsset", "type": "string"}
                ],
                "name": "IntentRegistered",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "intentId", "type": "bytes32"},
                    {"indexed": True, "name": "actor", "type": "address"}
                ],
                "name": "IntentCancelled",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "intentId", "type": "bytes32"},
                    {"indexed": True, "name": "actor", "type": "address"}
                ],
                "name": "IntentMatched",
                "type": "event"
            }
        ]

    def _get_auction_escrow_abi(self) -> List[dict]:
        """Get AuctionEscrow contract ABI"""
        return [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "matchId", "type": "bytes32"},
                    {"indexed": True, "name": "bidIntentId", "type": "bytes32"},
                    {"indexed": True, "name": "askIntentId", "type": "bytes32"},
                    {"indexed": False, "name": "bidder", "type": "address"},
                    {"indexed": False, "name": "asker", "type": "address"},
                    {"indexed": False, "name": "matchPrice", "type": "uint256"}
                ],
                "name": "MatchCreated",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "matchId", "type": "bytes32"},
                    {"indexed": False, "name": "ap2ProofHash", "type": "bytes32"}
                ],
                "name": "MatchSettled",
                "type": "event"
            }
        ]

    async def index_events(self, from_block: Optional[int] = None):
        """
        Index events from blockchain starting from specified block
        """
        if from_block is None:
            from_block = max(self.latest_block, self.w3.eth.block_number - 1000)

        to_block = self.w3.eth.block_number

        logger.info(f"Indexing events from block {from_block} to {to_block}")

        # Index IntentRegistry events
        await self._index_intent_registered(from_block, to_block)
        await self._index_intent_cancelled(from_block, to_block)
        await self._index_intent_matched(from_block, to_block)

        # Index AuctionEscrow events
        await self._index_match_created(from_block, to_block)
        await self._index_match_settled(from_block, to_block)

        self.latest_block = to_block
        self.session.commit()

        logger.info(f"Indexed up to block {to_block}")

    async def _index_intent_registered(self, from_block: int, to_block: int):
        """Index IntentRegistered events"""
        try:
            event_filter = self.intent_registry_contract.events.IntentRegistered.create_filter(
                fromBlock=from_block,
                toBlock=to_block
            )

            events = event_filter.get_all_entries()

            for event in events:
                args = event['args']
                intent_id = args['intentId'].hex()

                # Check if already indexed
                existing = self.session.query(IntentDB).filter_by(intent_id=intent_id).first()
                if existing:
                    continue

                intent = IntentDB(
                    intent_id=intent_id,
                    intent_hash=args['intentHash'].hex(),
                    actor=args['actor'],
                    timestamp=args['timestamp'],
                    valid_until=args['validUntil'],
                    ap2_mandate_id=args['ap2MandateId'].hex(),
                    settlement_asset=args['settlementAsset'],
                    is_active=True,
                    is_matched=False,
                    payload=json.dumps({})
                )

                self.session.add(intent)
                logger.info(f"Indexed intent: {intent_id}")

        except Exception as e:
            logger.error(f"Error indexing IntentRegistered events: {e}")

    async def _index_intent_cancelled(self, from_block: int, to_block: int):
        """Index IntentCancelled events"""
        try:
            event_filter = self.intent_registry_contract.events.IntentCancelled.create_filter(
                fromBlock=from_block,
                toBlock=to_block
            )

            events = event_filter.get_all_entries()

            for event in events:
                args = event['args']
                intent_id = args['intentId'].hex()

                intent = self.session.query(IntentDB).filter_by(intent_id=intent_id).first()
                if intent:
                    intent.is_active = False
                    logger.info(f"Cancelled intent: {intent_id}")

        except Exception as e:
            logger.error(f"Error indexing IntentCancelled events: {e}")

    async def _index_intent_matched(self, from_block: int, to_block: int):
        """Index IntentMatched events"""
        try:
            event_filter = self.intent_registry_contract.events.IntentMatched.create_filter(
                fromBlock=from_block,
                toBlock=to_block
            )

            events = event_filter.get_all_entries()

            for event in events:
                args = event['args']
                intent_id = args['intentId'].hex()

                intent = self.session.query(IntentDB).filter_by(intent_id=intent_id).first()
                if intent:
                    intent.is_matched = True
                    logger.info(f"Matched intent: {intent_id}")

        except Exception as e:
            logger.error(f"Error indexing IntentMatched events: {e}")

    async def _index_match_created(self, from_block: int, to_block: int):
        """Index MatchCreated events"""
        try:
            event_filter = self.auction_escrow_contract.events.MatchCreated.create_filter(
                fromBlock=from_block,
                toBlock=to_block
            )

            events = event_filter.get_all_entries()

            for event in events:
                args = event['args']
                match_id = args['matchId'].hex()

                existing = self.session.query(MatchDB).filter_by(match_id=match_id).first()
                if existing:
                    continue

                block = self.w3.eth.get_block(event['blockNumber'])

                match = MatchDB(
                    match_id=match_id,
                    bid_intent_id=args['bidIntentId'].hex(),
                    ask_intent_id=args['askIntentId'].hex(),
                    bidder=args['bidder'],
                    asker=args['asker'],
                    match_price=args['matchPrice'],
                    created_at=block['timestamp'],
                    settle_by=block['timestamp'] + 172800,  # 48 hours
                    status="pending"
                )

                self.session.add(match)
                logger.info(f"Indexed match: {match_id}")

        except Exception as e:
            logger.error(f"Error indexing MatchCreated events: {e}")

    async def _index_match_settled(self, from_block: int, to_block: int):
        """Index MatchSettled events"""
        try:
            event_filter = self.auction_escrow_contract.events.MatchSettled.create_filter(
                fromBlock=from_block,
                toBlock=to_block
            )

            events = event_filter.get_all_entries()

            for event in events:
                args = event['args']
                match_id = args['matchId'].hex()

                match = self.session.query(MatchDB).filter_by(match_id=match_id).first()
                if match:
                    match.status = "settled"
                    match.ap2_proof_hash = args['ap2ProofHash'].hex()
                    logger.info(f"Settled match: {match_id}")

        except Exception as e:
            logger.error(f"Error indexing MatchSettled events: {e}")

    async def run(self, poll_interval: int = 10):
        """
        Run indexer continuously
        """
        logger.info(f"Starting indexer with {poll_interval}s poll interval")

        while True:
            try:
                await self.index_events()
                await asyncio.sleep(poll_interval)
            except KeyboardInterrupt:
                logger.info("Indexer stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in indexer loop: {e}")
                await asyncio.sleep(poll_interval)

    def query_intents(
        self,
        actor: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_matched: Optional[bool] = None
    ) -> List[IntentDB]:
        """Query intents from database"""
        query = self.session.query(IntentDB)

        if actor:
            query = query.filter_by(actor=actor)
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        if is_matched is not None:
            query = query.filter_by(is_matched=is_matched)

        return query.all()

    def query_matches(
        self,
        status: Optional[str] = None,
        bidder: Optional[str] = None,
        asker: Optional[str] = None
    ) -> List[MatchDB]:
        """Query matches from database"""
        query = self.session.query(MatchDB)

        if status:
            query = query.filter_by(status=status)
        if bidder:
            query = query.filter_by(bidder=bidder)
        if asker:
            query = query.filter_by(asker=asker)

        return query.all()


async def main():
    """Main entry point"""
    rpc_url = os.getenv("ARC_TESTNET_RPC_URL", "http://localhost:8545")
    intent_registry = os.getenv("INTENT_REGISTRY_ADDRESS", "0x0")
    auction_escrow = os.getenv("AUCTION_ESCROW_ADDRESS", "0x0")

    indexer = ArcIndexer(rpc_url, intent_registry, auction_escrow)
    await indexer.run()


if __name__ == "__main__":
    asyncio.run(main())
