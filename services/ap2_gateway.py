"""
AP2 Gateway - Stripe Integration for Payment Verification
Implements Agent Payments Protocol (AP2) using Stripe as payment rail
"""
import os
from typing import Optional, Dict
from datetime import datetime, timedelta
import stripe
from loguru import logger
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv("config/.env")


class AP2Gateway:
    """
    AP2 Gateway for payment credential verification using Stripe
    Handles mandate registration, payment verification, and on-chain anchoring
    """

    def __init__(
        self,
        stripe_api_key: str,
        rpc_url: str,
        payment_router_address: str,
        oracle_private_key: str
    ):
        # Initialize Stripe
        stripe.api_key = stripe_api_key
        self.stripe = stripe

        # Initialize Web3 for on-chain verification recording
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.payment_router_address = Web3.to_checksum_address(payment_router_address)
        self.oracle_account = Account.from_key(oracle_private_key)

        # In-memory mandate registry (in production, use database)
        self.mandates: Dict[str, Dict] = {}

        logger.info("AP2 Gateway initialized with Stripe integration")

    def register_mandate(
        self,
        mandate_id: str,
        issuer: str,
        subject: str,
        scope: str,
        valid_until: datetime,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Register an AP2 payment mandate

        Args:
            mandate_id: Unique mandate identifier
            issuer: Issuer address
            subject: Subject (payer) address
            scope: Payment scope/authorization
            valid_until: Mandate expiration
            metadata: Additional metadata

        Returns:
            Mandate data
        """
        mandate = {
            "mandate_id": mandate_id,
            "issuer": issuer,
            "subject": subject,
            "scope": scope,
            "valid_from": datetime.now(),
            "valid_until": valid_until,
            "is_revoked": False,
            "metadata": metadata or {}
        }

        self.mandates[mandate_id] = mandate

        logger.info(f"Registered mandate: {mandate_id}")
        return mandate

    def verify_mandate(self, mandate_id: str) -> bool:
        """
        Verify if a mandate is valid and not revoked
        """
        if mandate_id not in self.mandates:
            logger.warning(f"Mandate not found: {mandate_id}")
            return False

        mandate = self.mandates[mandate_id]

        if mandate["is_revoked"]:
            logger.warning(f"Mandate revoked: {mandate_id}")
            return False

        if datetime.now() > mandate["valid_until"]:
            logger.warning(f"Mandate expired: {mandate_id}")
            return False

        return True

    def revoke_mandate(self, mandate_id: str):
        """Revoke an AP2 mandate"""
        if mandate_id in self.mandates:
            self.mandates[mandate_id]["is_revoked"] = True
            logger.info(f"Revoked mandate: {mandate_id}")

    async def create_payment_intent(
        self,
        amount: int,
        currency: str,
        payer: str,
        payee: str,
        mandate_id: str,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Create a Stripe payment intent for AP2 settlement

        Args:
            amount: Amount in smallest currency unit (e.g., cents for USD)
            currency: Currency code (e.g., "usd")
            payer: Payer address
            payee: Payee address
            mandate_id: AP2 mandate ID
            metadata: Additional metadata

        Returns:
            Payment intent data or None on failure
        """
        # Verify mandate
        if not self.verify_mandate(mandate_id):
            logger.error(f"Invalid mandate: {mandate_id}")
            return None

        try:
            payment_intent = self.stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                metadata={
                    "payer": payer,
                    "payee": payee,
                    "mandate_id": mandate_id,
                    **(metadata or {})
                },
                description=f"AP2 payment from {payer} to {payee}"
            )

            logger.info(
                f"Created payment intent: {payment_intent.id} "
                f"for {amount} {currency}"
            )

            return {
                "payment_intent_id": payment_intent.id,
                "amount": amount,
                "currency": currency,
                "status": payment_intent.status,
                "client_secret": payment_intent.client_secret
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {e}")
            return None

    async def verify_payment(
        self,
        payment_intent_id: str,
        expected_amount: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Verify a Stripe payment has been completed

        Args:
            payment_intent_id: Stripe payment intent ID
            expected_amount: Expected payment amount (optional validation)

        Returns:
            Payment verification data or None if invalid
        """
        try:
            payment_intent = self.stripe.PaymentIntent.retrieve(payment_intent_id)

            if payment_intent.status != "succeeded":
                logger.warning(
                    f"Payment not succeeded: {payment_intent_id} "
                    f"(status: {payment_intent.status})"
                )
                return None

            if expected_amount and payment_intent.amount < expected_amount:
                logger.error(
                    f"Payment amount insufficient: {payment_intent.amount} "
                    f"< {expected_amount}"
                )
                return None

            # Extract metadata
            payer = payment_intent.metadata.get("payer")
            payee = payment_intent.metadata.get("payee")
            mandate_id = payment_intent.metadata.get("mandate_id")

            verification = {
                "payment_intent_id": payment_intent_id,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "payer": payer,
                "payee": payee,
                "mandate_id": mandate_id,
                "verified": True,
                "timestamp": datetime.now().timestamp()
            }

            logger.info(f"Payment verified: {payment_intent_id}")

            return verification

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error verifying payment: {e}")
            return None

    async def anchor_payment_onchain(
        self,
        payment_intent_id: str,
        amount: int,
        payer: str,
        payee: str,
        mandate_id: str
    ) -> Optional[str]:
        """
        Anchor payment verification to blockchain via PaymentRouter

        Args:
            payment_intent_id: Stripe payment intent ID
            amount: Payment amount
            payer: Payer address
            payee: Payee address
            mandate_id: AP2 mandate ID

        Returns:
            Transaction hash or None on failure
        """
        try:
            # Load PaymentRouter contract
            contract = self.w3.eth.contract(
                address=self.payment_router_address,
                abi=self._get_payment_router_abi()
            )

            # Convert mandate_id to bytes32
            mandate_bytes = bytes.fromhex(mandate_id) if mandate_id.startswith("0x") else bytes.fromhex("0x" + mandate_id)

            # Prepare transaction
            tx = contract.functions.recordPaymentVerification(
                payment_intent_id,
                amount,
                Web3.to_checksum_address(payer),
                Web3.to_checksum_address(payee),
                mandate_bytes
            ).build_transaction({
                'from': self.oracle_account.address,
                'nonce': self.w3.eth.get_transaction_count(self.oracle_account.address),
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price
            })

            # Sign and send
            signed_tx = self.oracle_account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            logger.info(f"Payment anchored on-chain. Tx: {tx_hash.hex()}")

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt['status'] == 1:
                logger.info(f"Payment verification confirmed: {tx_hash.hex()}")
                return tx_hash.hex()
            else:
                logger.error(f"Payment verification transaction failed: {tx_hash.hex()}")
                return None

        except Exception as e:
            logger.error(f"Error anchoring payment on-chain: {e}")
            return None

    def _get_payment_router_abi(self):
        """Get PaymentRouter contract ABI"""
        return [
            {
                "inputs": [
                    {"name": "_stripePaymentIntentId", "type": "string"},
                    {"name": "_amount", "type": "uint256"},
                    {"name": "_payer", "type": "address"},
                    {"name": "_payee", "type": "address"},
                    {"name": "_ap2MandateId", "type": "bytes32"}
                ],
                "name": "recordPaymentVerification",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]

    async def process_payment_flow(
        self,
        amount: int,
        currency: str,
        payer: str,
        payee: str,
        mandate_id: str
    ) -> Optional[Dict]:
        """
        Complete AP2 payment flow: create intent, verify, anchor on-chain

        Returns:
            Complete payment data with on-chain tx hash
        """
        # Create payment intent
        intent = await self.create_payment_intent(
            amount, currency, payer, payee, mandate_id
        )

        if not intent:
            return None

        # In a real system, wait for user to complete payment
        # For demo, we'll simulate immediate verification
        logger.info(
            f"Payment intent created: {intent['payment_intent_id']}. "
            "Waiting for payment completion..."
        )

        # Verify payment (in production, this would be called by webhook)
        verification = await self.verify_payment(intent['payment_intent_id'], amount)

        if not verification:
            return None

        # Anchor verification on-chain
        tx_hash = await self.anchor_payment_onchain(
            intent['payment_intent_id'],
            amount,
            payer,
            payee,
            mandate_id
        )

        return {
            **intent,
            **verification,
            "tx_hash": tx_hash
        }


async def main():
    """Test AP2 Gateway"""
    stripe_key = os.getenv("STRIPE_API_KEY", "sk_test_xxx")
    rpc_url = os.getenv("ARC_TESTNET_RPC_URL", "http://localhost:8545")
    payment_router = os.getenv("PAYMENT_ROUTER_ADDRESS", "0x0")
    oracle_key = os.getenv("PRIVATE_KEY")

    gateway = AP2Gateway(stripe_key, rpc_url, payment_router, oracle_key)

    # Register test mandate
    mandate_id = "0x" + "1" * 64
    gateway.register_mandate(
        mandate_id,
        issuer="0x123...",
        subject="0x456...",
        scope="payment.create",
        valid_until=datetime.now() + timedelta(days=365)
    )

    logger.info("AP2 Gateway ready")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
