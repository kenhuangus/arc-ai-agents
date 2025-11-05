# Payment Integration Quick Start

## 🔑 Which Agent Needs Private Key?

**Answer: Settlement Agent**

The **Settlement Agent** is the merchant agent that:
- Receives payments for services
- Verifies payment signatures
- Settles transactions on-chain
- Delivers services after payment confirmation

---

## ⚡ Quick Setup

### 1. Install Dependencies

```bash
pip install x402-a2a web3 eth-account
```

### 2. Configure Environment

Add to `config/.env`:

```bash
# Payment Wallet (Settlement Agent)
PAYMENT_PRIVATE_KEY=0x...           # Your wallet private key
PAYMENT_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
PAYMENT_CHAIN_ID=1                  # 1=Ethereum, 137=Polygon

# Payment Limits
MIN_PAYMENT_AMOUNT=0.001            # Minimum 0.001 ETH
MAX_PAYMENT_AMOUNT=10.0             # Maximum 10 ETH
PAYMENT_TIMEOUT_SECONDS=300         # 5 minutes

# Gas Configuration
MAX_GAS_PRICE_GWEI=50
GAS_PRICE_MULTIPLIER=1.1
```

### 3. Payment Flow

```
Client Request → 402 Payment Required → Client Signs Payment →
Verify Signature → Settle On-Chain → Deliver Service
```

### 4. Code Example

```python
# In Settlement Agent

# Step 1: Request payment (402)
payment_request = self.payment_service.create_payment_request(
    amount_eth=0.01,
    service_id="match_12345",
    description="Settlement service for intent match"
)

# Step 2: Client submits signed payment
# (happens on client side)

# Step 3: Verify and settle
payment_result = self.payment_service.settle_payment_onchain(
    payment_submission
)

# Step 4: Deliver service
if payment_result["type"] == "payment-completed":
    # Execute settlement
    settlement_result = await self.execute_settlement(context)
```

---

## 🔒 Security Checklist

✅ Use environment variables for private key
✅ Never commit `.env` to git (already in `.gitignore`)
✅ Use testnet first (Goerli, Sepolia)
✅ Limit wallet funds in production
✅ Monitor wallet balance
✅ Validate all payment signatures
✅ Set reasonable payment limits

---

## 📚 Full Documentation

See **[A2A_X402_INTEGRATION_GUIDE.md](./A2A_X402_INTEGRATION_GUIDE.md)** for:
- Complete implementation code
- Payment service class
- Testing procedures
- Security best practices
- Deployment checklist
- Monitoring and logging

---

## 🎯 Key Points

1. **Settlement Agent** = Payment receiver (merchant)
2. **Needs private key** to sign settlement transactions
3. **Three-step flow**: Request → Verify → Settle
4. **x402 protocol** = Standard for agent payments
5. **On-chain verification** before service delivery

---

**Quick Start**: Read [A2A_X402_INTEGRATION_GUIDE.md](./A2A_X402_INTEGRATION_GUIDE.md)
**Full Spec**: https://x402.gitbook.io/x402
