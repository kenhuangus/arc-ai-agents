# A2A x402 Payment Integration Guide

## Overview

This guide explains how to integrate the **A2A x402 Extension** for cryptocurrency payments into the Arc AI Agents system, enabling agents to charge for their services on-chain.

---

## 🎯 Goal

Enable **agent commerce** by allowing agents to:
- Charge for API calls and services
- Receive payments on-chain
- Verify payments before delivering services
- Support cryptocurrency payment workflows

---

## 🏗️ Architecture Overview

### Which Agent Needs Private Key?

**Answer: Settlement Agent**

The **Settlement Agent** should handle payments because it:
1. **Already coordinates settlements** - Natural fit for payment execution
2. **Interacts with blockchain** - Has blockchain integration logic
3. **Executes final transactions** - Responsible for on-chain operations
4. **Manages multi-party coordination** - Can handle payment parties

### Payment Flow Integration

```
┌─────────────────────────────────────────────────────────┐
│              Client Agent (Buyer)                        │
│                                                          │
│  1. Request Service                                      │
│     ↓                                                    │
│  2. Receive Payment Required (402)                       │
│     ↓                                                    │
│  3. Sign Payment with Private Key                        │
│     ↓                                                    │
│  4. Submit Payment                                       │
│     ↓                                                    │
│  5. Receive Service + Payment Receipt                    │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│         Merchant Agent (Settlement Agent)                │
│                                                          │
│  1. Receive Service Request                              │
│     ↓                                                    │
│  2. Send Payment Required Message                        │
│     ↓                                                    │
│  3. Receive Payment Submission                           │
│     ↓                                                    │
│  4. Verify Payment Signature                             │
│     ↓                                                    │
│  5. Settle Payment On-Chain (with private key)           │
│     ↓                                                    │
│  6. Deliver Service + Payment Completed                  │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Required Dependencies

Add to `requirements.txt`:

```python
# A2A x402 Payment Protocol
x402-a2a>=0.1.0
web3>=6.0.0
eth-account>=0.11.0
python-dotenv>=1.0.0

# Optional: For Google A2A integration
google-auth>=2.23.0
google-auth-oauthlib>=1.1.0
google-auth-httplib2>=0.1.1
```

Install:
```bash
pip install x402-a2a web3 eth-account python-dotenv
```

---

## 🔐 Environment Configuration

Update `config/.env`:

```bash
# Existing API Keys
ANTHROPIC_API_KEY=sk-ant-api03-...
GOOGLE_API_KEY=AIza...

# Payment Configuration (NEW)
PAYMENT_PRIVATE_KEY=0x...  # Private key for settlement agent wallet
PAYMENT_CHAIN_ID=1         # 1 = Ethereum mainnet, 137 = Polygon, etc.
PAYMENT_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY

# Optional: Payment Gateway
PAYMENT_GATEWAY_URL=https://payment-gateway.arc.network
PAYMENT_MERCHANT_ID=merchant_arc_settlement_agent

# Gas Configuration
MAX_GAS_PRICE_GWEI=50
GAS_PRICE_MULTIPLIER=1.1

# Payment Limits
MIN_PAYMENT_AMOUNT=0.001   # ETH
MAX_PAYMENT_AMOUNT=10.0    # ETH
PAYMENT_TIMEOUT_SECONDS=300

# Optional: Multi-chain support
POLYGON_RPC_URL=https://polygon-rpc.com
BASE_RPC_URL=https://mainnet.base.org
ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc
```

**⚠️ Security Warning**:
- NEVER commit `.env` to git (already in `.gitignore`)
- Use environment-specific keys (dev vs prod)
- Consider using a key management service (AWS KMS, HashiCorp Vault)
- Use a separate payment wallet with limited funds

---

## 🛠️ Implementation

### 1. Create Payment Service

Create `services/payment/x402_service.py`:

```python
"""
A2A x402 Payment Service

Handles cryptocurrency payments using the x402 protocol.
"""

import os
import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from web3 import Web3
from eth_account import Account
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


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
        timeout_seconds: int = 300
    ):
        """
        Initialize payment service

        Args:
            private_key: Hex string private key (with or without 0x prefix)
            rpc_url: Blockchain RPC endpoint
            chain_id: Chain ID (1=Ethereum, 137=Polygon, etc.)
            min_amount: Minimum payment amount in ETH
            max_amount: Maximum payment amount in ETH
            timeout_seconds: Payment timeout
        """
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.chain_id = chain_id

        # Load account from private key
        if not private_key.startswith('0x'):
            private_key = f'0x{private_key}'
        self.account = Account.from_key(private_key)
        self.address = self.account.address

        self.min_amount = Decimal(str(min_amount))
        self.max_amount = Decimal(str(max_amount))
        self.timeout_seconds = timeout_seconds

        logger.info(f"Payment service initialized for address: {self.address}")
        logger.info(f"Chain ID: {chain_id}, Connected: {self.web3.is_connected()}")

    def create_payment_request(
        self,
        amount_eth: float,
        service_id: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a payment-required message (Step 1)

        Args:
            amount_eth: Payment amount in ETH
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

        # Convert to Wei
        amount_wei = self.web3.to_wei(amount, 'ether')

        # Create payment request
        payment_request = {
            "type": "payment-required",
            "version": "0.1",
            "timestamp": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=self.timeout_seconds)).isoformat(),
            "payment": {
                "amount": str(amount_wei),
                "currency": "ETH",
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

        logger.info(f"Created payment request: {service_id}, amount: {amount} ETH")
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

            # Reconstruct message that was signed
            message_hash = Web3.keccak(text=str(payment))

            # Recover signer address
            recovered_address = Account.recover_message(
                message_hash,
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

    def settle_payment_onchain(
        self,
        payment_submission: Dict[str, Any],
        max_gas_price_gwei: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Settle payment on-chain (Step 3)

        Args:
            payment_submission: Verified payment submission
            max_gas_price_gwei: Maximum gas price in Gwei

        Returns:
            Payment completed message with transaction hash
        """
        try:
            payment = payment_submission["payment"]
            payer_address = payment_submission["payer"]["address"]
            amount_wei = int(payment["amount"])

            # Check balance
            payer_balance = self.web3.eth.get_balance(payer_address)
            if payer_balance < amount_wei:
                raise ValueError(f"Insufficient balance: {payer_balance} < {amount_wei}")

            # Prepare transaction
            nonce = self.web3.eth.get_transaction_count(self.address)

            # Gas price with multiplier
            gas_price = self.web3.eth.gas_price
            multiplier = float(os.getenv("GAS_PRICE_MULTIPLIER", "1.1"))
            gas_price = int(gas_price * multiplier)

            # Apply max gas price limit
            if max_gas_price_gwei:
                max_gas_wei = self.web3.to_wei(max_gas_price_gwei, 'gwei')
                gas_price = min(gas_price, max_gas_wei)

            # Build transaction
            tx = {
                'nonce': nonce,
                'to': self.address,  # Payment to settlement agent
                'value': amount_wei,
                'gas': 21000,  # Standard ETH transfer
                'gasPrice': gas_price,
                'chainId': self.chain_id,
                'from': payer_address
            }

            # Note: In production, the payer would sign and send this
            # For now, we're simulating merchant-side settlement

            # Sign transaction (merchant signs for accounting)
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.account.key)

            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()

            # Wait for confirmation
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            # Create payment completed message
            payment_completed = {
                "type": "payment-completed",
                "version": "0.1",
                "timestamp": datetime.utcnow().isoformat(),
                "transaction": {
                    "hash": tx_hash_hex,
                    "block_number": receipt['blockNumber'],
                    "gas_used": receipt['gasUsed'],
                    "status": "success" if receipt['status'] == 1 else "failed"
                },
                "payment": payment,
                "settlement": {
                    "confirmed": receipt['status'] == 1,
                    "confirmations": 1,
                    "finalized": False  # Wait for more confirmations
                }
            }

            logger.info(f"Payment settled on-chain: {tx_hash_hex}")
            return payment_completed

        except Exception as e:
            logger.error(f"Error settling payment: {e}")
            return {
                "type": "payment-failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def get_balance(self) -> Decimal:
        """Get merchant wallet balance in ETH"""
        balance_wei = self.web3.eth.get_balance(self.address)
        balance_eth = self.web3.from_wei(balance_wei, 'ether')
        return Decimal(str(balance_eth))

    @classmethod
    def from_env(cls) -> 'X402PaymentService':
        """Create payment service from environment variables"""
        return cls(
            private_key=os.getenv("PAYMENT_PRIVATE_KEY"),
            rpc_url=os.getenv("PAYMENT_RPC_URL"),
            chain_id=int(os.getenv("PAYMENT_CHAIN_ID", "1")),
            min_amount=float(os.getenv("MIN_PAYMENT_AMOUNT", "0.001")),
            max_amount=float(os.getenv("MAX_PAYMENT_AMOUNT", "10.0")),
            timeout_seconds=int(os.getenv("PAYMENT_TIMEOUT_SECONDS", "300"))
        )
```

### 2. Update Settlement Agent

Modify `services/agents/settlement_agent.py` to use the payment service:

```python
# Add to imports at top of file
from services.payment.x402_service import X402PaymentService
import os

# Add to SettlementAgent.__init__
def __init__(self):
    super().__init__(
        name="settlement_agent",
        description="Coordinates settlement execution for matched intents",
        model_preference=ModelPreference.CLAUDE
    )

    # Initialize payment service if configured
    if os.getenv("PAYMENT_PRIVATE_KEY"):
        try:
            self.payment_service = X402PaymentService.from_env()
            logger.info("Payment service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize payment service: {e}")
            self.payment_service = None
    else:
        logger.warning("PAYMENT_PRIVATE_KEY not configured - payments disabled")
        self.payment_service = None

# Add new method to SettlementAgent class
async def request_payment(
    self,
    amount_eth: float,
    match_id: str,
    description: str
) -> Dict[str, Any]:
    """
    Request payment from client using x402 protocol

    Returns payment-required message
    """
    if not self.payment_service:
        raise ValueError("Payment service not configured")

    return self.payment_service.create_payment_request(
        amount_eth=amount_eth,
        service_id=match_id,
        description=description,
        metadata={
            "agent": "settlement_agent",
            "workflow": "intent_settlement"
        }
    )

async def verify_and_settle_payment(
    self,
    payment_submission: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify payment signature and settle on-chain

    Returns payment-completed message with transaction hash
    """
    if not self.payment_service:
        raise ValueError("Payment service not configured")

    # Step 1: Verify signature
    if not self.payment_service.verify_payment_signature(payment_submission):
        return {
            "type": "payment-failed",
            "error": "Invalid payment signature",
            "timestamp": datetime.utcnow().isoformat()
        }

    # Step 2: Settle on-chain
    max_gas_gwei = int(os.getenv("MAX_GAS_PRICE_GWEI", "50"))
    return self.payment_service.settle_payment_onchain(
        payment_submission,
        max_gas_price_gwei=max_gas_gwei
    )
```

### 3. Add Payment Tools

Create `services/langgraph/payment_tools.py`:

```python
"""
Payment tools for LangGraph agents
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def create_payment_request_tool(payment_service) -> callable:
    """Create a tool for requesting payments"""

    async def request_payment(
        amount_eth: float,
        service_id: str,
        description: str
    ) -> Dict[str, Any]:
        """
        Request payment from client (x402 payment-required)

        Args:
            amount_eth: Payment amount in ETH
            service_id: Service identifier
            description: Payment description

        Returns:
            Payment request message
        """
        try:
            return payment_service.create_payment_request(
                amount_eth=amount_eth,
                service_id=service_id,
                description=description
            )
        except Exception as e:
            logger.error(f"Payment request error: {e}")
            return {"error": str(e)}

    return request_payment


def create_payment_verification_tool(payment_service) -> callable:
    """Create a tool for verifying payments"""

    async def verify_payment(
        payment_submission: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify payment signature and settle on-chain

        Args:
            payment_submission: Payment submission from client

        Returns:
            Payment completed message with transaction hash
        """
        try:
            # Verify signature
            if not payment_service.verify_payment_signature(payment_submission):
                return {
                    "verified": False,
                    "error": "Invalid signature"
                }

            # Settle on-chain
            result = payment_service.settle_payment_onchain(payment_submission)
            return result

        except Exception as e:
            logger.error(f"Payment verification error: {e}")
            return {"error": str(e)}

    return verify_payment
```

---

## 🔄 Payment Flow Example

### Scenario: Charging for Intent Matching

```python
# In Settlement Agent

async def process_settlement_with_payment(
    self,
    context: AgentContext
) -> AgentResult:
    """
    Process settlement with payment requirement
    """

    # Step 1: Calculate service fee
    match = context.previous_results.get("matching", {})
    amount_eth = 0.01  # Charge 0.01 ETH per match

    # Step 2: Request payment (402)
    payment_request = await self.request_payment(
        amount_eth=amount_eth,
        match_id=match.get("match_id", "unknown"),
        description=f"Settlement service for match {match.get('match_id')}"
    )

    # Return payment-required to client
    return AgentResult(
        success=False,  # Not complete yet
        data={
            "payment_required": True,
            "payment_request": payment_request
        },
        reasoning="Payment required before settlement execution"
    )

async def handle_payment_submission(
    self,
    payment_submission: Dict[str, Any],
    context: AgentContext
) -> AgentResult:
    """
    Handle payment submission from client
    """

    # Verify and settle payment
    payment_result = await self.verify_and_settle_payment(payment_submission)

    if payment_result.get("type") == "payment-completed":
        # Payment successful - proceed with settlement
        logger.info(f"Payment completed: {payment_result['transaction']['hash']}")

        # Execute actual settlement
        settlement_result = await self.execute_settlement(context)

        return AgentResult(
            success=True,
            data={
                "payment": payment_result,
                "settlement": settlement_result
            },
            reasoning="Payment verified and settlement completed"
        )
    else:
        # Payment failed
        return AgentResult(
            success=False,
            data={
                "payment_failed": True,
                "error": payment_result.get("error")
            },
            reasoning="Payment verification failed"
        )
```

---

## 🧪 Testing

Create `tests/test_payment_service.py`:

```python
"""
Tests for x402 payment service
"""

import pytest
import os
from services.payment.x402_service import X402PaymentService

# Use testnet for testing
TEST_RPC_URL = "https://goerli.infura.io/v3/YOUR_KEY"
TEST_CHAIN_ID = 5  # Goerli testnet


def test_payment_service_init():
    """Test payment service initialization"""
    service = X402PaymentService(
        private_key=os.getenv("TEST_PRIVATE_KEY"),
        rpc_url=TEST_RPC_URL,
        chain_id=TEST_CHAIN_ID
    )

    assert service.web3.is_connected()
    assert service.address.startswith("0x")
    print(f"✅ Payment service initialized: {service.address}")


def test_create_payment_request():
    """Test creating payment request"""
    service = X402PaymentService(
        private_key=os.getenv("TEST_PRIVATE_KEY"),
        rpc_url=TEST_RPC_URL,
        chain_id=TEST_CHAIN_ID
    )

    payment_request = service.create_payment_request(
        amount_eth=0.01,
        service_id="test_match_001",
        description="Test settlement service"
    )

    assert payment_request["type"] == "payment-required"
    assert "payment" in payment_request
    assert float(payment_request["payment"]["amount"]) > 0
    print(f"✅ Payment request created: {payment_request['payment']['service_id']}")


def test_get_balance():
    """Test getting wallet balance"""
    service = X402PaymentService(
        private_key=os.getenv("TEST_PRIVATE_KEY"),
        rpc_url=TEST_RPC_URL,
        chain_id=TEST_CHAIN_ID
    )

    balance = service.get_balance()
    print(f"✅ Wallet balance: {balance} ETH")
    assert balance >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

Run tests:
```bash
# Set test private key (testnet wallet)
export TEST_PRIVATE_KEY=0x...

# Run tests
pytest tests/test_payment_service.py -v
```

---

## 📚 API Documentation

### Payment Request (402)

```json
{
  "type": "payment-required",
  "version": "0.1",
  "timestamp": "2025-01-05T10:30:00Z",
  "expires_at": "2025-01-05T10:35:00Z",
  "payment": {
    "amount": "10000000000000000",  // Wei (0.01 ETH)
    "currency": "ETH",
    "chain_id": 1,
    "recipient": "0xSettlementAgentAddress",
    "service_id": "match_12345",
    "description": "Settlement service for intent match",
    "metadata": {
      "agent": "settlement_agent",
      "workflow": "intent_settlement"
    }
  },
  "merchant": {
    "name": "Arc Settlement Agent",
    "address": "0xSettlementAgentAddress",
    "url": "https://payment-gateway.arc.network"
  }
}
```

### Payment Submission

```json
{
  "type": "payment-submitted",
  "version": "0.1",
  "timestamp": "2025-01-05T10:30:15Z",
  "payment": {
    // ... same as payment-required
  },
  "payer": {
    "address": "0xClientAddress",
    "name": "Client Agent"
  },
  "signature": "0x..."  // Signed by client's private key
}
```

### Payment Completed

```json
{
  "type": "payment-completed",
  "version": "0.1",
  "timestamp": "2025-01-05T10:30:45Z",
  "transaction": {
    "hash": "0x123abc...",
    "block_number": 12345678,
    "gas_used": 21000,
    "status": "success"
  },
  "payment": {
    // ... same as original payment
  },
  "settlement": {
    "confirmed": true,
    "confirmations": 1,
    "finalized": false
  }
}
```

---

## 🔒 Security Best Practices

### 1. Private Key Management

```python
# ❌ BAD - Never hardcode keys
PAYMENT_PRIVATE_KEY = "0x123abc..."

# ✅ GOOD - Use environment variables
PAYMENT_PRIVATE_KEY = os.getenv("PAYMENT_PRIVATE_KEY")

# ✅ BETTER - Use key management service
import boto3
kms = boto3.client('kms')
private_key = kms.decrypt(CiphertextBlob=encrypted_key)
```

### 2. Wallet Separation

```
Development:  Use testnet wallets (Goerli, Sepolia)
Staging:      Use separate testnet wallet
Production:   Dedicated production wallet with limited funds
```

### 3. Payment Validation

```python
# Always validate
- Signature authenticity
- Payment amount matches request
- Payment not expired
- Sufficient balance
- No replay attacks (use nonce)
```

### 4. Error Handling

```python
try:
    payment_result = await settle_payment(payment_submission)
except InsufficientFundsError:
    # Refund or notify
except NetworkError:
    # Retry with backoff
except InvalidSignatureError:
    # Reject and log
```

---

## 🚀 Deployment Checklist

- [ ] Generate dedicated payment wallet
- [ ] Fund wallet with sufficient ETH for gas
- [ ] Configure `PAYMENT_PRIVATE_KEY` in production
- [ ] Set appropriate `MIN_PAYMENT_AMOUNT` and `MAX_PAYMENT_AMOUNT`
- [ ] Configure `MAX_GAS_PRICE_GWEI` to control costs
- [ ] Test payment flow on testnet first
- [ ] Monitor wallet balance alerts
- [ ] Set up transaction monitoring
- [ ] Configure payment webhooks (if using gateway)
- [ ] Document payment pricing for clients

---

## 📊 Monitoring

### Key Metrics

```python
# Track in production
- Payment requests created
- Payment success rate
- Average settlement time
- Gas costs per transaction
- Failed payment reasons
- Wallet balance over time
```

### Logging

```python
logger.info("Payment request created", extra={
    "service_id": service_id,
    "amount_eth": amount_eth,
    "recipient": self.address
})

logger.info("Payment settled", extra={
    "tx_hash": tx_hash,
    "block_number": block_number,
    "gas_used": gas_used,
    "payer": payer_address
})
```

---

## 🔗 Resources

- [x402 Protocol Specification](https://x402.gitbook.io/x402)
- [A2A Protocol](https://github.com/a2aproject/a2a-python)
- [x402 Python Library](https://github.com/x402/x402-a2a/tree/main/python)
- [Web3.py Documentation](https://web3py.readthedocs.io/)
- [Ethereum Gas Tracker](https://etherscan.io/gastracker)

---

## 🎯 Next Steps

1. **Install Dependencies**: Add x402-a2a to requirements.txt
2. **Configure Wallet**: Generate payment wallet and add to .env
3. **Implement Payment Service**: Create services/payment/x402_service.py
4. **Update Settlement Agent**: Add payment methods
5. **Test on Testnet**: Use Goerli or Sepolia
6. **Monitor & Deploy**: Set up monitoring and deploy to production

---

**Built with**: A2A x402 Protocol • Web3.py • Ethereum • Arc AI Agents

**Status**: Ready for Integration

**Last Updated**: 2025-01-05
