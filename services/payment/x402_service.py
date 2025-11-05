"""
A2A x402 Payment Service

Handles cryptocurrency payments using the x402 protocol.

Implements the three-step payment flow:
1. payment-required: Merchant requests payment
2. payment-submitted: Client signs and submits payment
3. payment-completed: Merchant verifies and settles on-chain
"""

import os
import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta

try:
    from web3 import Web3
    from eth_account import Account
    from eth_account.messages import encode_defunct
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logging.warning("web3 or eth-account not installed. Payment functionality will be disabled.")

logger = logging.getLogger(__name__)

# Standard ERC-20 ABI (minimal interface)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    }
]


class X402PaymentService:
    """
    Service for handling x402 payments

    Implements the three-step payment flow:
    1. payment-required: Merchant requests payment
    2. payment-submitted: Client signs and submits payment
    3. payment-completed: Merchant verifies and settles on-chain
    """

    def __init__(
        self,
        private_key: str,
        rpc_url: str,
        chain_id: int = 1,
        min_amount: float = 0.001,
        max_amount: float = 10.0,
        timeout_seconds: int = 300,
        currency_type: str = "NATIVE",
        token_address: Optional[str] = None,
        token_symbol: Optional[str] = None,
        token_decimals: Optional[int] = None
    ):
        """
        Initialize payment service

        Args:
            private_key: Hex string private key (with or without 0x prefix)
            rpc_url: Blockchain RPC endpoint
            chain_id: Chain ID (1=Ethereum, 137=Polygon, etc.)
            min_amount: Minimum payment amount (in ETH for NATIVE, in token units for ERC20)
            max_amount: Maximum payment amount (in ETH for NATIVE, in token units for ERC20)
            timeout_seconds: Payment timeout
            currency_type: "NATIVE" for ETH/native currency, "ERC20" for token payments
            token_address: ERC-20 token contract address (required if currency_type is ERC20)
            token_symbol: Token symbol (e.g., "USDC", required if currency_type is ERC20)
            token_decimals: Token decimals (e.g., 6 for USDC, required if currency_type is ERC20)
        """
        if not WEB3_AVAILABLE:
            raise ImportError(
                "web3 and eth-account are required for payment functionality. "
                "Install with: pip install web3 eth-account"
            )

        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.chain_id = chain_id
        self.currency_type = currency_type.upper()

        # Load account from private key
        if not private_key.startswith('0x'):
            private_key = f'0x{private_key}'
        self.account = Account.from_key(private_key)
        self.address = self.account.address

        self.min_amount = Decimal(str(min_amount))
        self.max_amount = Decimal(str(max_amount))
        self.timeout_seconds = timeout_seconds

        # Initialize token contract for ERC-20 payments
        self.token_contract = None
        self.token_address = None
        self.token_symbol = "ETH"  # Default
        self.token_decimals = 18  # Default for ETH

        if self.currency_type == "ERC20":
            if not token_address or not token_symbol or token_decimals is None:
                raise ValueError(
                    "token_address, token_symbol, and token_decimals are required for ERC20 currency type"
                )

            # Validate token address format
            if not Web3.is_address(token_address):
                raise ValueError(f"Invalid token address: {token_address}")

            self.token_address = Web3.to_checksum_address(token_address)
            self.token_symbol = token_symbol
            self.token_decimals = token_decimals

            # Load token contract
            self.token_contract = self.web3.eth.contract(
                address=self.token_address,
                abi=ERC20_ABI
            )

            logger.info(f"Payment service initialized for ERC-20: {token_symbol} at {self.token_address}")
        else:
            logger.info(f"Payment service initialized for native currency (ETH)")

        logger.info(f"Merchant address: {self.address}")
        logger.info(f"Chain ID: {chain_id}, Connected: {self.web3.is_connected()}")

    def create_payment_request(
        self,
        amount_eth: float,  # Kept for backward compatibility, but can be any currency amount
        service_id: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a payment-required message (Step 1)

        Args:
            amount_eth: Payment amount (in ETH for NATIVE, in token units for ERC20)
            service_id: Unique identifier for the service
            description: Human-readable description
            metadata: Additional metadata

        Returns:
            Payment request message compatible with x402 protocol
        """
        amount = Decimal(str(amount_eth))

        # Validate amount
        if amount < self.min_amount:
            raise ValueError(f"Amount {amount} below minimum {self.min_amount}")
        if amount > self.max_amount:
            raise ValueError(f"Amount {amount} above maximum {self.max_amount}")

        # Convert to base units (Wei for ETH, smallest unit for tokens)
        # For ETH: 18 decimals, for USDC: 6 decimals
        amount_base = int(amount * (10 ** self.token_decimals))

        # Create payment request
        payment_request = {
            "type": "payment-required",
            "version": "0.1",
            "timestamp": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=self.timeout_seconds)).isoformat(),
            "payment": {
                "amount": str(amount_base),
                "currency": self.token_symbol,
                "currency_type": self.currency_type,
                "chain_id": self.chain_id,
                "recipient": self.address,
                "service_id": service_id,
                "description": description,
                "metadata": metadata or {}
            },
            "merchant": {
                "name": "Arc Settlement Agent",
                "address": self.address,
                "url": os.getenv("PAYMENT_GATEWAY_URL", "")
            }
        }

        # Add token address for ERC-20 payments
        if self.currency_type == "ERC20":
            payment_request["payment"]["token_address"] = self.token_address
            payment_request["payment"]["token_decimals"] = self.token_decimals

        logger.info(f"Created payment request: {service_id}, amount: {amount} {self.token_symbol}")
        return payment_request

    def verify_payment_signature(
        self,
        payment_submission: Dict[str, Any]
    ) -> bool:
        """
        Verify payment signature from client (Step 2)

        Args:
            payment_submission: Payment-submitted message with signature

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Extract payment details
            payment = payment_submission.get("payment", {})
            signature = payment_submission.get("signature", "")
            payer_address = payment_submission.get("payer", {}).get("address", "")

            if not signature or not payer_address:
                logger.warning("Missing signature or payer address")
                return False

            # Reconstruct message that was signed
            import json
            message_text = json.dumps(payment, sort_keys=True)
            message = encode_defunct(text=message_text)

            # Recover signer address
            recovered_address = Account.recover_message(
                message,
                signature=signature
            )

            # Verify signer matches payer
            is_valid = recovered_address.lower() == payer_address.lower()

            if is_valid:
                logger.info(f"Payment signature verified for {payer_address}")
            else:
                logger.warning(f"Invalid signature from {payer_address}")

            return is_valid

        except Exception as e:
            logger.error(f"Error verifying payment signature: {e}")
            return False

    def verify_transaction_received(
        self,
        tx_hash: str,
        payment_submission: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify that payment transaction was received (Step 3)

        In the x402 protocol, the payer sends the transaction.
        The merchant verifies it was received correctly.

        Args:
            tx_hash: Transaction hash sent by the payer
            payment_submission: Verified payment submission

        Returns:
            Payment completed message with verification status
        """
        try:
            payment = payment_submission["payment"]
            payer_address = payment_submission["payer"]["address"]
            expected_amount_base = int(payment["amount"])

            # Get transaction receipt
            receipt = self.web3.eth.get_transaction_receipt(tx_hash)

            if not receipt:
                raise ValueError(f"Transaction {tx_hash} not found")

            # Check transaction succeeded
            if receipt['status'] != 1:
                raise ValueError("Transaction failed on-chain")

            # Get transaction details
            tx = self.web3.eth.get_transaction(tx_hash)

            # Verify transaction sender
            if tx['from'].lower() != payer_address.lower():
                raise ValueError(f"Payment from wrong address: {tx['from']} != {payer_address}")

            # Verify payment based on currency type
            if self.currency_type == "ERC20":
                # For ERC-20, verify Transfer event in receipt logs
                # Transfer event signature: Transfer(address indexed from, address indexed to, uint256 value)
                transfer_event_signature = self.web3.keccak(text="Transfer(address,address,uint256)").hex()

                transfer_found = False
                for log in receipt['logs']:
                    # Check if this is a Transfer event from the token contract
                    if (log['address'].lower() == self.token_address.lower() and
                        len(log['topics']) > 0 and
                        log['topics'][0].hex() == transfer_event_signature):

                        # Decode Transfer event
                        # topics[0] = event signature
                        # topics[1] = from address
                        # topics[2] = to address
                        # data = amount
                        from_addr = '0x' + log['topics'][1].hex()[-40:]
                        to_addr = '0x' + log['topics'][2].hex()[-40:]
                        amount = int(log['data'].hex(), 16)

                        # Verify transfer details
                        if (from_addr.lower() == payer_address.lower() and
                            to_addr.lower() == self.address.lower() and
                            amount == expected_amount_base):
                            transfer_found = True
                            break

                if not transfer_found:
                    raise ValueError(
                        f"No valid Transfer event found. Expected {expected_amount_base} {self.token_symbol} "
                        f"from {payer_address} to {self.address}"
                    )

                logger.info(f"ERC-20 payment verified: {expected_amount_base} {self.token_symbol} from {payer_address}")

            else:
                # For native currency, verify transaction value and recipient
                if tx['to'].lower() != self.address.lower():
                    raise ValueError(f"Payment sent to wrong address: {tx['to']} != {self.address}")

                if tx['value'] != expected_amount_base:
                    raise ValueError(f"Payment amount mismatch: {tx['value']} != {expected_amount_base}")

                logger.info(f"Native payment verified: {expected_amount_base} wei from {payer_address}")

            # Create payment completed message
            payment_completed = {
                "type": "payment-completed",
                "version": "0.1",
                "timestamp": datetime.utcnow().isoformat(),
                "transaction": {
                    "hash": tx_hash,
                    "block_number": receipt['blockNumber'],
                    "gas_used": receipt['gasUsed'],
                    "status": "success"
                },
                "payment": payment,
                "settlement": {
                    "confirmed": True,
                    "confirmations": 1,
                    "finalized": False  # Wait for more confirmations
                }
            }

            logger.info(f"Payment verified on-chain: {tx_hash}")
            return payment_completed

        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return {
                "type": "payment-failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def prepare_payment_transaction(
        self,
        payment_submission: Dict[str, Any],
        max_gas_price_gwei: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Prepare transaction data for payer to sign and send (Step 3 helper)

        This method creates the transaction parameters that the payer
        should use to send payment on-chain.

        Args:
            payment_submission: Verified payment submission
            max_gas_price_gwei: Maximum gas price in Gwei

        Returns:
            Transaction parameters for payer to sign and send
        """
        try:
            payment = payment_submission["payment"]
            payer_address = payment_submission["payer"]["address"]
            amount_base = int(payment["amount"])

            # Get payer's nonce
            nonce = self.web3.eth.get_transaction_count(payer_address)

            # Gas price with multiplier
            gas_price = self.web3.eth.gas_price
            multiplier = float(os.getenv("GAS_PRICE_MULTIPLIER", "1.1"))
            gas_price = int(gas_price * multiplier)

            # Apply max gas price limit
            if max_gas_price_gwei:
                max_gas_wei = self.web3.to_wei(max_gas_price_gwei, 'gwei')
                gas_price = min(gas_price, max_gas_wei)

            # Build transaction based on currency type
            if self.currency_type == "ERC20":
                # Check token balance
                token_balance = self.token_contract.functions.balanceOf(payer_address).call()
                if token_balance < amount_base:
                    raise ValueError(
                        f"Insufficient token balance: {token_balance} < {amount_base} "
                        f"({token_balance / (10 ** self.token_decimals):.{self.token_decimals}f} {self.token_symbol})"
                    )

                # Build ERC-20 transfer transaction
                transfer_function = self.token_contract.functions.transfer(
                    self.address,  # recipient (merchant)
                    amount_base    # amount in base units
                )

                tx_params = {
                    'nonce': nonce,
                    'to': self.token_address,  # Send to token contract
                    'value': 0,  # No native value for ERC-20 transfer
                    'gas': 65000,  # ERC-20 transfer gas (higher than ETH)
                    'gasPrice': gas_price,
                    'chainId': self.chain_id,
                    'data': transfer_function._encode_transaction_data()  # ERC-20 transfer() call data
                }

                logger.info(f"Prepared ERC-20 payment: {payer_address} -> {self.address}, {amount_base} {self.token_symbol}")

            else:
                # Native currency (ETH) transfer
                # Check balance
                payer_balance = self.web3.eth.get_balance(payer_address)
                if payer_balance < amount_base:
                    raise ValueError(f"Insufficient balance: {payer_balance} < {amount_base}")

                # Build native transfer transaction
                tx_params = {
                    'nonce': nonce,
                    'to': self.address,  # Payment to merchant
                    'value': amount_base,
                    'gas': 21000,  # Standard ETH transfer
                    'gasPrice': gas_price,
                    'chainId': self.chain_id
                }

                logger.info(f"Prepared native payment: {payer_address} -> {self.address}, {amount_base} wei")

            return {
                "type": "transaction-prepared",
                "transaction": tx_params,
                "instructions": "Sign this transaction with your private key and broadcast to the network"
            }

        except Exception as e:
            logger.error(f"Error preparing transaction: {e}")
            raise

    def get_balance(self) -> Decimal:
        """Get merchant wallet balance (ETH for NATIVE, token balance for ERC20)"""
        if self.currency_type == "ERC20":
            # Get token balance
            balance_base = self.token_contract.functions.balanceOf(self.address).call()
            balance_token = Decimal(balance_base) / Decimal(10 ** self.token_decimals)
            logger.info(f"Token balance: {balance_token} {self.token_symbol}")
            return balance_token
        else:
            # Get native balance
            balance_wei = self.web3.eth.get_balance(self.address)
            balance_eth = self.web3.from_wei(balance_wei, 'ether')
            logger.info(f"Native balance: {balance_eth} ETH")
            return Decimal(str(balance_eth))

    def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction status

        Args:
            tx_hash: Transaction hash

        Returns:
            Transaction status information
        """
        try:
            receipt = self.web3.eth.get_transaction_receipt(tx_hash)
            return {
                "found": True,
                "status": "success" if receipt['status'] == 1 else "failed",
                "block_number": receipt['blockNumber'],
                "gas_used": receipt['gasUsed']
            }
        except Exception as e:
            logger.error(f"Error getting transaction status: {e}")
            return {
                "found": False,
                "error": str(e)
            }

    @classmethod
    def from_env(cls) -> 'X402PaymentService':
        """
        Create payment service from environment variables

        Required env vars:
        - PAYMENT_PRIVATE_KEY: Private key for payment wallet
        - PAYMENT_RPC_URL: RPC endpoint URL
        - PAYMENT_CHAIN_ID: Chain ID (default: 1)

        Optional env vars:
        - MIN_PAYMENT_AMOUNT: Minimum payment amount (default: 0.001)
        - MAX_PAYMENT_AMOUNT: Maximum payment amount (default: 10.0)
        - PAYMENT_TIMEOUT_SECONDS: Payment timeout (default: 300)
        - PAYMENT_CURRENCY_TYPE: "NATIVE" or "ERC20" (default: "NATIVE")

        For ERC20 payments (required if PAYMENT_CURRENCY_TYPE=ERC20):
        - PAYMENT_TOKEN_ADDRESS: Token contract address
        - PAYMENT_TOKEN_SYMBOL: Token symbol (e.g., "USDC")
        - PAYMENT_TOKEN_DECIMALS: Token decimals (e.g., 6 for USDC)
        """
        private_key = os.getenv("PAYMENT_PRIVATE_KEY")
        rpc_url = os.getenv("PAYMENT_RPC_URL")

        if not private_key:
            raise ValueError("PAYMENT_PRIVATE_KEY environment variable not set")
        if not rpc_url:
            raise ValueError("PAYMENT_RPC_URL environment variable not set")

        # Load currency type
        currency_type = os.getenv("PAYMENT_CURRENCY_TYPE", "NATIVE").upper()

        # Load token configuration for ERC20
        token_address = os.getenv("PAYMENT_TOKEN_ADDRESS")
        token_symbol = os.getenv("PAYMENT_TOKEN_SYMBOL")
        token_decimals_str = os.getenv("PAYMENT_TOKEN_DECIMALS")
        token_decimals = int(token_decimals_str) if token_decimals_str else None

        # Validate ERC20 configuration
        if currency_type == "ERC20":
            if not token_address or not token_symbol or token_decimals is None:
                raise ValueError(
                    "For ERC20 payments, PAYMENT_TOKEN_ADDRESS, PAYMENT_TOKEN_SYMBOL, "
                    "and PAYMENT_TOKEN_DECIMALS must be set"
                )

        return cls(
            private_key=private_key,
            rpc_url=rpc_url,
            chain_id=int(os.getenv("PAYMENT_CHAIN_ID", "1")),
            min_amount=float(os.getenv("MIN_PAYMENT_AMOUNT", "0.001")),
            max_amount=float(os.getenv("MAX_PAYMENT_AMOUNT", "10.0")),
            timeout_seconds=int(os.getenv("PAYMENT_TIMEOUT_SECONDS", "300")),
            currency_type=currency_type,
            token_address=token_address,
            token_symbol=token_symbol,
            token_decimals=token_decimals
        )


# Mock payment service for testing without web3
class MockX402PaymentService:
    """Mock payment service for testing without blockchain connectivity"""

    def __init__(self, *args, **kwargs):
        self.address = "0xMockMerchantAddress"
        self.currency_type = kwargs.get('currency_type', 'NATIVE')
        self.token_symbol = kwargs.get('token_symbol', 'ETH')
        self.token_decimals = kwargs.get('token_decimals', 18)
        logger.warning("Using mock payment service - no actual payments will be processed")

    def create_payment_request(self, amount_eth: float, service_id: str,
                              description: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create mock payment request"""
        return {
            "type": "payment-required",
            "version": "0.1",
            "timestamp": datetime.utcnow().isoformat(),
            "payment": {
                "amount": str(int(amount_eth * 1e18)),
                "currency": "ETH",
                "service_id": service_id,
                "description": description,
                "recipient": self.address
            },
            "merchant": {
                "name": "Arc Settlement Agent (Mock)",
                "address": self.address
            }
        }

    def verify_payment_signature(self, payment_submission: Dict[str, Any]) -> bool:
        """Mock verification - always returns True"""
        logger.info("Mock payment verification - always succeeds")
        return True

    def prepare_payment_transaction(self, payment_submission: Dict[str, Any],
                                   max_gas_price_gwei: Optional[int] = None) -> Dict[str, Any]:
        """Mock transaction preparation"""
        return {
            "type": "transaction-prepared",
            "transaction": {
                "to": self.address,
                "value": payment_submission.get("payment", {}).get("amount", "0"),
                "gas": 21000
            },
            "instructions": "Mock transaction - no actual blockchain interaction"
        }

    def verify_transaction_received(self, tx_hash: str,
                                    payment_submission: Dict[str, Any]) -> Dict[str, Any]:
        """Mock transaction verification"""
        return {
            "type": "payment-completed",
            "version": "0.1",
            "timestamp": datetime.utcnow().isoformat(),
            "transaction": {
                "hash": tx_hash or "0xMockTransactionHash",
                "block_number": 12345678,
                "gas_used": 21000,
                "status": "success"
            },
            "payment": payment_submission.get("payment", {}),
            "settlement": {
                "confirmed": True,
                "confirmations": 1,
                "finalized": False
            }
        }

    def get_balance(self) -> Decimal:
        """Mock balance"""
        return Decimal("1.0")

    @classmethod
    def from_env(cls) -> 'MockX402PaymentService':
        """Create mock service"""
        return cls()
