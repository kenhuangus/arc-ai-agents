"""
Auction-based Matching Engine for Arc Coordination System
Implements bid/ask matching logic with price discovery
"""
import asyncio
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from enum import Enum
import heapq
from loguru import logger
from web3 import Web3
from eth_account import Account
import os
from dotenv import load_dotenv

load_dotenv("config/.env")


class IntentType(Enum):
    """Intent type enum"""
    BID = "bid"  # Buy-side
    ASK = "ask"  # Sell-side


@dataclass
class OrderBookEntry:
    """Order book entry for matching"""
    intent_id: str
    actor: str
    price: int  # Price in smallest currency unit
    quantity: int
    intent_type: IntentType
    timestamp: int
    settlement_asset: str
    ap2_mandate_id: str

    def __lt__(self, other):
        """Comparison for heap operations"""
        if self.intent_type == IntentType.BID:
            # Bids: higher price has priority
            return self.price > other.price
        else:
            # Asks: lower price has priority
            return self.price < other.price


class AuctionEngine:
    """
    Auction-based matching engine with continuous double auction (CDA) algorithm
    """

    def __init__(
        self,
        rpc_url: str,
        auction_escrow_address: str,
        private_key: str,
        indexer
    ):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.auction_escrow_address = Web3.to_checksum_address(auction_escrow_address)
        self.account = Account.from_key(private_key)
        self.indexer = indexer

        # Order books: separate heaps for bids and asks by asset
        self.bid_books: Dict[str, List[OrderBookEntry]] = {}  # asset -> max heap
        self.ask_books: Dict[str, List[OrderBookEntry]] = {}  # asset -> min heap

        # Matched pairs awaiting on-chain settlement
        self.pending_matches: List[Tuple[str, str, int]] = []

        logger.info("Auction engine initialized")

    def add_intent(self, entry: OrderBookEntry):
        """Add an intent to the order book"""
        asset = entry.settlement_asset

        if entry.intent_type == IntentType.BID:
            if asset not in self.bid_books:
                self.bid_books[asset] = []
            heapq.heappush(self.bid_books[asset], entry)
            logger.info(f"Added BID intent {entry.intent_id} at price {entry.price}")

        else:  # ASK
            if asset not in self.ask_books:
                self.ask_books[asset] = []
            heapq.heappush(self.ask_books[asset], entry)
            logger.info(f"Added ASK intent {entry.intent_id} at price {entry.price}")

    def try_match(self, asset: str) -> Optional[Tuple[OrderBookEntry, OrderBookEntry, int]]:
        """
        Try to match best bid with best ask for given asset
        Returns (bid_entry, ask_entry, match_price) or None
        """
        if asset not in self.bid_books or asset not in self.ask_books:
            return None

        if not self.bid_books[asset] or not self.ask_books[asset]:
            return None

        best_bid = self.bid_books[asset][0]
        best_ask = self.ask_books[asset][0]

        # Check if bid price >= ask price (orders can cross)
        if best_bid.price >= best_ask.price:
            # Match found! Determine settlement price
            # Use mid-price for fairness
            match_price = (best_bid.price + best_ask.price) // 2

            # Remove from heaps
            heapq.heappop(self.bid_books[asset])
            heapq.heappop(self.ask_books[asset])

            logger.info(
                f"Match found: BID {best_bid.intent_id} @ {best_bid.price} "
                f"<-> ASK {best_ask.intent_id} @ {best_ask.price} "
                f"| Settlement: {match_price}"
            )

            return (best_bid, best_ask, match_price)

        return None

    async def match_continuously(self, asset: str):
        """
        Continuously try to match orders for a given asset
        """
        while True:
            match_result = self.try_match(asset)

            if match_result:
                bid_entry, ask_entry, match_price = match_result

                # Create match on-chain
                await self.create_match_onchain(
                    bid_entry.intent_id,
                    ask_entry.intent_id,
                    match_price
                )

            else:
                # No more matches possible
                break

    async def create_match_onchain(
        self,
        bid_intent_id: str,
        ask_intent_id: str,
        match_price: int
    ) -> Optional[str]:
        """
        Create a match on-chain via AuctionEscrow contract
        """
        try:
            # Load contract ABI (simplified)
            contract = self.w3.eth.contract(
                address=self.auction_escrow_address,
                abi=self._get_escrow_abi()
            )

            # Prepare transaction
            tx = contract.functions.createMatch(
                bytes.fromhex(bid_intent_id),
                bytes.fromhex(ask_intent_id),
                match_price
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price
            })

            # Sign and send
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            logger.info(f"Match created on-chain. Tx: {tx_hash.hex()}")

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt['status'] == 1:
                logger.info(f"Match confirmed: {tx_hash.hex()}")
                return tx_hash.hex()
            else:
                logger.error(f"Match transaction failed: {tx_hash.hex()}")
                return None

        except Exception as e:
            logger.error(f"Error creating match on-chain: {e}")
            return None

    def _get_escrow_abi(self) -> List[dict]:
        """Get AuctionEscrow contract ABI for createMatch function"""
        return [
            {
                "inputs": [
                    {"name": "_bidIntentId", "type": "bytes32"},
                    {"name": "_askIntentId", "type": "bytes32"},
                    {"name": "_matchPrice", "type": "uint256"}
                ],
                "name": "createMatch",
                "outputs": [{"name": "matchId", "type": "bytes32"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]

    async def load_intents_from_indexer(self):
        """
        Load active, unmatched intents from indexer and populate order books
        """
        logger.info("Loading intents from indexer...")

        intents = self.indexer.query_intents(is_active=True, is_matched=False)

        for intent_db in intents:
            # Parse intent payload to extract price and type
            # For demo, assume constraints contain "type" and "price"
            import json
            payload = json.loads(intent_db.payload) if intent_db.payload else {}
            constraints = payload.get("constraints", {})

            intent_type_str = constraints.get("type", "bid")
            price = constraints.get("price", 0)
            quantity = constraints.get("quantity", 1)

            if price == 0:
                continue  # Skip intents without price

            intent_type = IntentType.BID if intent_type_str.lower() == "bid" else IntentType.ASK

            entry = OrderBookEntry(
                intent_id=intent_db.intent_id,
                actor=intent_db.actor,
                price=price,
                quantity=quantity,
                intent_type=intent_type,
                timestamp=intent_db.timestamp,
                settlement_asset=intent_db.settlement_asset,
                ap2_mandate_id=intent_db.ap2_mandate_id
            )

            self.add_intent(entry)

        logger.info(
            f"Loaded {len(intents)} intents. "
            f"Bid books: {sum(len(v) for v in self.bid_books.values())}, "
            f"Ask books: {sum(len(v) for v in self.ask_books.values())}"
        )

    async def run_matching_loop(self, poll_interval: int = 10):
        """
        Continuously run the matching engine
        """
        logger.info(f"Starting matching engine with {poll_interval}s interval")

        while True:
            try:
                # Reload intents from indexer
                await self.load_intents_from_indexer()

                # Try matching for each asset
                all_assets = set(self.bid_books.keys()) | set(self.ask_books.keys())

                for asset in all_assets:
                    await self.match_continuously(asset)

                await asyncio.sleep(poll_interval)

            except KeyboardInterrupt:
                logger.info("Matching engine stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in matching loop: {e}")
                await asyncio.sleep(poll_interval)

    def get_order_book_snapshot(self, asset: str) -> Dict:
        """Get current order book snapshot for an asset"""
        bids = sorted(
            self.bid_books.get(asset, []),
            key=lambda x: x.price,
            reverse=True
        )[:10]  # Top 10 bids

        asks = sorted(
            self.ask_books.get(asset, []),
            key=lambda x: x.price
        )[:10]  # Top 10 asks

        return {
            "asset": asset,
            "bids": [
                {"intent_id": b.intent_id, "price": b.price, "quantity": b.quantity}
                for b in bids
            ],
            "asks": [
                {"intent_id": a.intent_id, "price": a.price, "quantity": a.quantity}
                for a in asks
            ],
            "spread": asks[0].price - bids[0].price if bids and asks else None
        }


async def main():
    """Main entry point"""
    from services.indexer import ArcIndexer

    rpc_url = os.getenv("ARC_TESTNET_RPC_URL", "http://localhost:8545")
    escrow_address = os.getenv("AUCTION_ESCROW_ADDRESS", "0x0")
    private_key = os.getenv("PRIVATE_KEY")
    intent_registry = os.getenv("INTENT_REGISTRY_ADDRESS", "0x0")

    # Initialize indexer
    indexer = ArcIndexer(rpc_url, intent_registry, escrow_address)

    # Initialize engine
    engine = AuctionEngine(rpc_url, escrow_address, private_key, indexer)

    # Run matching loop
    await engine.run_matching_loop()


if __name__ == "__main__":
    asyncio.run(main())
