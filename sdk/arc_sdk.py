"""
Arc Coordination System Python SDK
Provides high-level interface for intent lifecycle management
"""
import os
import json
import hashlib
from typing import Dict, List, Optional
from datetime import datetime
import httpx
from web3 import Web3
from eth_account import Account
from loguru import logger


class ArcSDK:
    """
    Python SDK for Arc Coordination System

    Provides methods for:
    - Intent submission and management
    - Match querying and settlement
    - Payment processing
    - Mandate management
    """

    def __init__(
        self,
        api_base_url: str,
        rpc_url: str,
        private_key: str,
        intent_registry_address: str,
        auction_escrow_address: str,
        payment_router_address: str
    ):
        """
        Initialize Arc SDK

        Args:
            api_base_url: Base URL of Arc API
            rpc_url: Arc RPC endpoint
            private_key: Private key for signing transactions
            intent_registry_address: IntentRegistry contract address
            auction_escrow_address: AuctionEscrow contract address
            payment_router_address: PaymentRouter contract address
        """
        self.api_base_url = api_base_url.rstrip("/")
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = Account.from_key(private_key)

        self.intent_registry_address = Web3.to_checksum_address(intent_registry_address)
        self.auction_escrow_address = Web3.to_checksum_address(auction_escrow_address)
        self.payment_router_address = Web3.to_checksum_address(payment_router_address)

        self.http_client = httpx.AsyncClient(timeout=30.0)

        logger.info(f"Arc SDK initialized for address: {self.account.address}")

    # Intent Methods

    async def submit_intent(
        self,
        intent_payload: Dict,
        valid_until: int,
        ap2_mandate_id: str,
        settlement_asset: str,
        constraints: Optional[Dict] = None
    ) -> Dict:
        """
        Submit a new intent to the coordination system

        Args:
            intent_payload: Intent data
            valid_until: Unix timestamp for expiration
            ap2_mandate_id: AP2 mandate ID
            settlement_asset: Asset for settlement (e.g., "USD", "ETH")
            constraints: Additional constraints

        Returns:
            Intent submission result with intent_id and tx_hash
        """
        try:
            response = await self.http_client.post(
                f"{self.api_base_url}/intents/submit",
                json={
                    "intent_payload": intent_payload,
                    "valid_until": valid_until,
                    "ap2_mandate_id": ap2_mandate_id,
                    "settlement_asset": settlement_asset,
                    "constraints": constraints or {}
                }
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Intent submitted: {result['intent_id']}")
            return result

        except httpx.HTTPError as e:
            logger.error(f"Error submitting intent: {e}")
            raise

    async def get_intent(self, intent_id: str) -> Dict:
        """Get intent details by ID"""
        try:
            response = await self.http_client.get(
                f"{self.api_base_url}/intents/{intent_id}"
            )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error getting intent: {e}")
            raise

    async def list_intents(
        self,
        actor: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_matched: Optional[bool] = None
    ) -> List[Dict]:
        """
        List intents with optional filters

        Args:
            actor: Filter by actor address
            is_active: Filter by active status
            is_matched: Filter by matched status

        Returns:
            List of intents
        """
        try:
            params = {}
            if actor:
                params["actor"] = actor
            if is_active is not None:
                params["is_active"] = is_active
            if is_matched is not None:
                params["is_matched"] = is_matched

            response = await self.http_client.get(
                f"{self.api_base_url}/intents",
                params=params
            )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error listing intents: {e}")
            raise

    async def cancel_intent(self, intent_id: str) -> Dict:
        """Cancel an active intent"""
        try:
            response = await self.http_client.post(
                f"{self.api_base_url}/intents/{intent_id}/cancel"
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Intent cancelled: {intent_id}")
            return result

        except httpx.HTTPError as e:
            logger.error(f"Error cancelling intent: {e}")
            raise

    # Match Methods

    async def get_match(self, match_id: str) -> Dict:
        """Get match details by ID"""
        try:
            response = await self.http_client.get(
                f"{self.api_base_url}/matches/{match_id}"
            )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error getting match: {e}")
            raise

    async def list_matches(
        self,
        status: Optional[str] = None,
        bidder: Optional[str] = None,
        asker: Optional[str] = None
    ) -> List[Dict]:
        """
        List matches with optional filters

        Args:
            status: Filter by match status
            bidder: Filter by bidder address
            asker: Filter by asker address

        Returns:
            List of matches
        """
        try:
            params = {}
            if status:
                params["status"] = status
            if bidder:
                params["bidder"] = bidder
            if asker:
                params["asker"] = asker

            response = await self.http_client.get(
                f"{self.api_base_url}/matches",
                params=params
            )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error listing matches: {e}")
            raise

    async def fund_escrow(self, match_id: str, amount: int) -> Dict:
        """
        Fund escrow for a match

        Args:
            match_id: Match ID
            amount: Amount in wei

        Returns:
            Transaction result
        """
        try:
            contract = self.w3.eth.contract(
                address=self.auction_escrow_address,
                abi=self._get_escrow_abi()
            )

            tx = contract.functions.fundEscrow(
                bytes.fromhex(match_id)
            ).build_transaction({
                'from': self.account.address,
                'value': amount,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price
            })

            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            logger.info(f"Escrow funded for match {match_id}. Tx: {tx_hash.hex()}")

            return {
                "match_id": match_id,
                "tx_hash": tx_hash.hex(),
                "status": "success" if receipt['status'] == 1 else "failed"
            }

        except Exception as e:
            logger.error(f"Error funding escrow: {e}")
            raise

    # Payment Methods

    async def create_payment_intent(
        self,
        amount: int,
        currency: str,
        payer: str,
        payee: str,
        mandate_id: str
    ) -> Dict:
        """
        Create a Stripe payment intent

        Args:
            amount: Amount in smallest currency unit
            currency: Currency code (e.g., "usd")
            payer: Payer address
            payee: Payee address
            mandate_id: AP2 mandate ID

        Returns:
            Payment intent data
        """
        try:
            response = await self.http_client.post(
                f"{self.api_base_url}/payments/create-intent",
                params={
                    "amount": amount,
                    "currency": currency,
                    "payer": payer,
                    "payee": payee,
                    "mandate_id": mandate_id
                }
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Payment intent created: {result['payment_intent_id']}")
            return result

        except httpx.HTTPError as e:
            logger.error(f"Error creating payment intent: {e}")
            raise

    async def verify_payment(self, payment_intent_id: str) -> Dict:
        """Verify a payment and anchor on-chain"""
        try:
            response = await self.http_client.post(
                f"{self.api_base_url}/payments/verify",
                params={"payment_intent_id": payment_intent_id}
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Payment verified: {payment_intent_id}")
            return result

        except httpx.HTTPError as e:
            logger.error(f"Error verifying payment: {e}")
            raise

    # Mandate Methods

    async def register_mandate(
        self,
        mandate_id: str,
        issuer: str,
        subject: str,
        scope: str,
        valid_days: int = 365
    ) -> Dict:
        """Register an AP2 payment mandate"""
        try:
            response = await self.http_client.post(
                f"{self.api_base_url}/mandates/register",
                params={
                    "mandate_id": mandate_id,
                    "issuer": issuer,
                    "subject": subject,
                    "scope": scope,
                    "valid_days": valid_days
                }
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Mandate registered: {mandate_id}")
            return result

        except httpx.HTTPError as e:
            logger.error(f"Error registering mandate: {e}")
            raise

    # Order Book Methods

    async def get_orderbook(self, asset: str) -> Dict:
        """Get current order book for an asset"""
        try:
            response = await self.http_client.get(
                f"{self.api_base_url}/orderbook/{asset}"
            )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error getting order book: {e}")
            raise

    # Helper Methods

    def _get_escrow_abi(self):
        """Get AuctionEscrow contract ABI"""
        return [
            {
                "inputs": [{"name": "_matchId", "type": "bytes32"}],
                "name": "fundEscrow",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function"
            }
        ]

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Example usage
async def main():
    """Example SDK usage"""
    sdk = ArcSDK(
        api_base_url=os.getenv("API_BASE_URL", "http://localhost:8000"),
        rpc_url=os.getenv("ARC_TESTNET_RPC_URL", "http://localhost:8545"),
        private_key=os.getenv("PRIVATE_KEY"),
        intent_registry_address=os.getenv("INTENT_REGISTRY_ADDRESS", "0x0"),
        auction_escrow_address=os.getenv("AUCTION_ESCROW_ADDRESS", "0x0"),
        payment_router_address=os.getenv("PAYMENT_ROUTER_ADDRESS", "0x0")
    )

    try:
        # Submit an intent
        result = await sdk.submit_intent(
            intent_payload={"description": "Buy 100 tokens"},
            valid_until=int(datetime.now().timestamp()) + 3600,
            ap2_mandate_id="0x" + "1" * 64,
            settlement_asset="USD",
            constraints={"type": "bid", "price": 10000, "quantity": 100}
        )

        print(f"Intent submitted: {result}")

        # List intents
        intents = await sdk.list_intents(is_active=True, is_matched=False)
        print(f"Active intents: {len(intents)}")

    finally:
        await sdk.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
