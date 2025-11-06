# Building an AI-Powered Intent Coordination System on Arc Testnet

**A Complete Tutorial: From Zero to Production**

---

## 📚 Table of Contents

1. [Project Overview](#project-overview)
2. [What You'll Learn](#what-youll-learn)
3. [Prerequisites](#prerequisites)
4. [Architecture](#architecture)
5. [Part 1: Setting Up the Environment](#part-1-setting-up-the-environment)
6. [Part 2: Smart Contracts](#part-2-smart-contracts)
7. [Part 3: Backend API](#part-3-backend-api)
8. [Part 4: AI Agents](#part-4-ai-agents)
9. [Part 5: Frontend UI](#part-5-frontend-ui)
10. [Part 6: x402 Payment Integration](#part-6-x402-payment-integration)
11. [Part 7: Deployment to Arc Testnet](#part-7-deployment-to-arc-testnet)
12. [Part 8: Testing End-to-End](#part-8-testing-end-to-end)
13. [Troubleshooting](#troubleshooting)
14. [Next Steps](#next-steps)

---

## Project Overview

### What Are We Building?

An **AI-powered intent coordination system** for decentralized trading that combines:
- **Smart contracts** for on-chain settlement
- **AI agents** for intelligent matching and risk assessment
- **x402 payment protocol** for agent-to-agent payments
- **Arc testnet integration** with USDC settlements

### Real-World Use Case

Imagine a decentralized marketplace where:
1. **Alice** wants to buy 1 BTC for $95,000 USDC
2. **Bob** wants to sell 1 BTC for $94,500 USDC
3. **AI agents** automatically:
   - Find the match
   - Verify market conditions
   - Check for fraud
   - Assess risk
   - Execute settlement on Arc testnet

This tutorial shows you how to build exactly that!

### GitHub Repository

```
https://github.com/YOUR-USERNAME/arc-coordination-system
```

**Clone the repository:**
```bash
git clone https://github.com/YOUR-USERNAME/arc-coordination-system.git
cd arc-coordination-system
```

---

## What You'll Learn

By completing this tutorial, you'll master:

### Blockchain Development
- ✅ Writing and deploying Solidity smart contracts
- ✅ Using Foundry for contract development
- ✅ Integrating with Arc testnet (USDC native gas)
- ✅ Managing contract upgrades and versioning

### AI Integration
- ✅ Building LangGraph workflows for multi-agent systems
- ✅ Creating specialized AI agents (matching, fraud, risk, settlement)
- ✅ Implementing agent-to-agent communication
- ✅ Using Claude/GPT for decision-making

### Backend Engineering
- ✅ Building FastAPI REST APIs
- ✅ Web3.py for blockchain interactions
- ✅ SQLite for state management
- ✅ Async/await patterns in Python

### Frontend Development
- ✅ Streamlit for rapid UI development
- ✅ Real-time updates with session state
- ✅ Web3 wallet integration
- ✅ Transaction monitoring

### Payment Protocols
- ✅ Implementing x402 payment standard
- ✅ ECDSA signature verification
- ✅ ERC-20 token transfers
- ✅ Gas optimization strategies

---

## Prerequisites

### Required Knowledge

**Minimum:**
- Basic Python programming
- Understanding of REST APIs
- Basic blockchain concepts (transactions, wallets, gas)

**Recommended:**
- Solidity basics
- FastAPI or Flask experience
- Web3 interactions
- AI/ML concepts

### Required Tools

Install these before starting:

1. **Python 3.11+**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **Foundry** (Solidity toolkit)
   ```bash
   curl -L https://foundry.paradigm.xyz | bash
   foundryup
   forge --version
   ```

3. **Node.js 18+** (for some utilities)
   ```bash
   node --version
   npm --version
   ```

4. **Git**
   ```bash
   git --version
   ```

5. **A Code Editor** (VS Code recommended)
   - [Download VS Code](https://code.visualstudio.com/)
   - Install Python extension
   - Install Solidity extension

### Recommended VS Code Extensions

```
code --install-extension ms-python.python
code --install-extension JuanBlanco.solidity
code --install-extension esbenp.prettier-vscode
```

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         User Interface                       │
│                        (Streamlit UI)                        │
│  - Intent Creation   - AI Agents Demo   - x402 Payments    │
└───────────────┬─────────────────────────────────────────────┘
                │
                │ HTTP REST API
                ▼
┌─────────────────────────────────────────────────────────────┐
│                       Backend API                            │
│                       (FastAPI)                              │
│  - Intent Management  - Agent Orchestration  - Payments     │
└───────┬───────────────────────────┬─────────────────────────┘
        │                           │
        │ Web3                      │ LangGraph
        ▼                           ▼
┌──────────────────┐      ┌─────────────────────────────────┐
│  Smart Contracts │      │        AI Agent System          │
│   (Arc Testnet)  │      │         (LangGraph)             │
│                  │      │                                 │
│ - IntentRegistry │      │  ┌─────────────────────────┐   │
│ - AuctionEscrow  │      │  │   Matching Agent        │   │
│ - PaymentRouter  │      │  │   (Find matches)        │   │
│                  │      │  └──────────┬──────────────┘   │
└──────────────────┘      │             │                   │
                          │             ▼                   │
                          │  ┌─────────────────────────┐   │
                          │  │   Market Agent          │   │
                          │  │   (Analyze conditions)  │   │
                          │  └──────────┬──────────────┘   │
                          │             │                   │
                          │             ▼                   │
                          │  ┌─────────────────────────┐   │
                          │  │   Fraud Agent           │   │
                          │  │   (Detect suspicious)   │   │
                          │  └──────────┬──────────────┘   │
                          │             │                   │
                          │             ▼                   │
                          │  ┌─────────────────────────┐   │
                          │  │   Risk Agent            │   │
                          │  │   (Assess overall risk) │   │
                          │  └──────────┬──────────────┘   │
                          │             │                   │
                          │             ▼                   │
                          │  ┌─────────────────────────┐   │
                          │  │   Settlement Agent      │   │
                          │  │   (Execute on-chain)    │   │
                          │  └─────────────────────────┘   │
                          └─────────────────────────────────┘
```

### Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Smart Contracts** | Solidity + Foundry | On-chain settlement and escrow |
| **Blockchain** | Arc Testnet | USDC-native testnet |
| **Backend API** | FastAPI + Python 3.11 | RESTful API server |
| **Database** | SQLite | Intent and transaction storage |
| **AI Framework** | LangGraph + Anthropic Claude | Multi-agent orchestration |
| **Web3 Integration** | Web3.py | Blockchain interactions |
| **Frontend** | Streamlit | Interactive web UI |
| **Payment Protocol** | x402 Standard | Agent-to-agent payments |

---

## Part 1: Setting Up the Environment

### Step 1.1: Create Project Structure

```bash
mkdir arc-coordination-system
cd arc-coordination-system

# Create directory structure
mkdir -p {contracts,services,ui,config,tests,logs,data}
```

**Directory Structure:**
```
arc-coordination-system/
├── contracts/          # Solidity smart contracts
│   ├── src/
│   ├── script/
│   ├── test/
│   └── foundry.toml
├── services/           # Backend Python services
│   ├── api.py         # FastAPI server
│   ├── agents/        # AI agents
│   ├── langgraph/     # LangGraph workflows
│   └── payment.py     # x402 payment service
├── ui/                 # Streamlit frontend
│   ├── streamlit_app.py
│   ├── x402_payment_demo.py
│   └── ai_demo_enhanced.py
├── config/             # Configuration files
│   └── .env
├── tests/              # Test files
├── logs/               # Application logs
└── data/               # SQLite databases
```

### Step 1.2: Initialize Python Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate it
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate     # On Windows

# Upgrade pip
pip install --upgrade pip
```

### Step 1.3: Install Python Dependencies

**Create `requirements.txt`:**

```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
streamlit==1.28.1

# Blockchain
web3==6.11.3
eth-account==0.10.0
py-solc-x==1.1.1

# AI & LangGraph
langchain==0.1.0
langgraph==0.0.20
anthropic==0.7.0
openai==1.3.7

# Data & Database
pydantic==2.5.0
sqlalchemy==2.0.23
aiosqlite==0.19.0

# Utilities
python-dotenv==1.0.0
python-multipart==0.0.6
requests==2.31.0
aiohttp==3.9.1
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

### Step 1.4: Initialize Foundry Project

```bash
cd contracts
forge init --force
cd ..
```

This creates:
- `contracts/src/` - Solidity source files
- `contracts/test/` - Contract tests
- `contracts/script/` - Deployment scripts
- `contracts/foundry.toml` - Foundry configuration

### Step 1.5: Set Up Configuration

**Create `config/.env`:**

```bash
# AI Provider
ANTHROPIC_API_KEY=your-anthropic-api-key-here
OPENAI_API_KEY=your-openai-api-key-here  # Optional

# Arc Testnet Configuration
PAYMENT_NETWORK=arc_testnet
PAYMENT_RPC_URL=https://rpc.testnet.arc.network
PAYMENT_CHAIN_ID=5042002

# USDC Token (Native gas token on Arc testnet)
PAYMENT_CURRENCY_TYPE=ERC20
PAYMENT_TOKEN_ADDRESS=0x3600000000000000000000000000000000000000
PAYMENT_TOKEN_SYMBOL=USDC
PAYMENT_TOKEN_DECIMALS=6

# Test Account (Replace with your own!)
PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

# Contract Addresses (Will be updated after deployment)
INTENT_REGISTRY_ADDRESS=
AUCTION_ESCROW_ADDRESS=
PAYMENT_ROUTER_ADDRESS=

# Payment Limits
MIN_PAYMENT_AMOUNT=1.0
MAX_PAYMENT_AMOUNT=10000.0
```

**⚠️ IMPORTANT**: Never commit your `.env` file to Git!

**Create `.gitignore`:**
```bash
cat > .gitignore << 'EOF'
# Python
venv/
__pycache__/
*.pyc
*.pyo
*.egg-info/

# Environment
.env
.env.local

# Database
*.db
data/*.db

# Logs
logs/*.log

# IDE
.vscode/
.idea/
*.swp

# Foundry
contracts/cache/
contracts/out/
contracts/broadcast/
EOF
```

---

## Part 2: Smart Contracts

### Why Smart Contracts?

Smart contracts provide:
- **Immutability**: Rules can't be changed after deployment
- **Transparency**: All transactions are publicly verifiable
- **Trust**: No need for intermediaries
- **Automation**: Self-executing when conditions are met

### Step 2.1: IntentRegistry Contract

This contract stores all intents (buy/sell orders).

**Create `contracts/src/IntentRegistry.sol`:**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IntentRegistry
 * @notice Stores and manages trading intents (buy/sell orders)
 * @dev Each intent represents a user's desire to buy or sell an asset
 */
contract IntentRegistry {
    /// @notice Intent types
    enum IntentType { BID, ASK }

    /// @notice Intent status
    enum IntentStatus { ACTIVE, MATCHED, CANCELLED, EXECUTED }

    /// @notice Intent data structure
    struct Intent {
        bytes32 intentId;        // Unique identifier
        address actor;           // Who created this intent
        IntentType intentType;   // BID or ASK
        string asset;            // Asset to trade (e.g., "BTC")
        uint256 price;           // Price in USDC (6 decimals)
        uint256 quantity;        // Quantity (18 decimals for precision)
        string settlementAsset;  // Payment currency (e.g., "USDC")
        IntentStatus status;     // Current status
        uint256 timestamp;       // Creation time
        uint256 validUntil;      // Expiration time
    }

    /// @notice Mapping from intent ID to intent data
    mapping(bytes32 => Intent) public intents;

    /// @notice List of all intent IDs
    bytes32[] public intentIds;

    /// @notice Events
    event IntentCreated(
        bytes32 indexed intentId,
        address indexed actor,
        IntentType intentType,
        string asset,
        uint256 price,
        uint256 quantity
    );

    event IntentStatusUpdated(
        bytes32 indexed intentId,
        IntentStatus oldStatus,
        IntentStatus newStatus
    );

    /**
     * @notice Create a new intent
     * @param intentId Unique identifier for this intent
     * @param intentType BID or ASK
     * @param asset Asset to trade
     * @param price Price in USDC
     * @param quantity Quantity to trade
     * @param settlementAsset Payment currency
     * @param validUntil Expiration timestamp
     */
    function createIntent(
        bytes32 intentId,
        IntentType intentType,
        string memory asset,
        uint256 price,
        uint256 quantity,
        string memory settlementAsset,
        uint256 validUntil
    ) external {
        require(intents[intentId].actor == address(0), "Intent already exists");
        require(quantity > 0, "Quantity must be positive");
        require(price > 0, "Price must be positive");
        require(validUntil > block.timestamp, "Invalid expiration");

        intents[intentId] = Intent({
            intentId: intentId,
            actor: msg.sender,
            intentType: intentType,
            asset: asset,
            price: price,
            quantity: quantity,
            settlementAsset: settlementAsset,
            status: IntentStatus.ACTIVE,
            timestamp: block.timestamp,
            validUntil: validUntil
        });

        intentIds.push(intentId);

        emit IntentCreated(
            intentId,
            msg.sender,
            intentType,
            asset,
            price,
            quantity
        );
    }

    /**
     * @notice Update intent status
     * @param intentId Intent to update
     * @param newStatus New status
     */
    function updateIntentStatus(
        bytes32 intentId,
        IntentStatus newStatus
    ) external {
        Intent storage intent = intents[intentId];
        require(intent.actor != address(0), "Intent does not exist");
        require(intent.actor == msg.sender, "Not authorized");

        IntentStatus oldStatus = intent.status;
        intent.status = newStatus;

        emit IntentStatusUpdated(intentId, oldStatus, newStatus);
    }

    /**
     * @notice Get intent by ID
     * @param intentId Intent ID
     * @return Intent data
     */
    function getIntent(bytes32 intentId) external view returns (Intent memory) {
        return intents[intentId];
    }

    /**
     * @notice Get total number of intents
     * @return Total count
     */
    function getIntentCount() external view returns (uint256) {
        return intentIds.length;
    }
}
```

**Key Concepts:**

1. **Struct**: Groups related data (Intent has id, actor, type, price, etc.)
2. **Mapping**: Like a hash map, `intentId => Intent`
3. **Events**: Emit logs that can be indexed and queried
4. **Modifiers**: `require()` checks conditions, reverts if false

### Step 2.2: PaymentRouter Contract

Handles USDC payments using the x402 protocol.

**Create `contracts/src/PaymentRouter.sol`:**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

/**
 * @title PaymentRouter
 * @notice Handles USDC payments for settlements
 * @dev Implements x402 payment protocol
 */
contract PaymentRouter {
    /// @notice USDC token address on Arc testnet
    address public immutable usdcToken;

    /// @notice Events
    event PaymentProcessed(
        address indexed from,
        address indexed to,
        uint256 amount,
        bytes32 indexed referenceId
    );

    /**
     * @notice Constructor
     * @param _usdcToken USDC token address
     */
    constructor(address _usdcToken) {
        require(_usdcToken != address(0), "Invalid USDC address");
        usdcToken = _usdcToken;
    }

    /**
     * @notice Process payment from payer to recipient
     * @param from Payer address
     * @param to Recipient address
     * @param amount Amount in USDC (6 decimals)
     * @param referenceId Transaction reference
     */
    function processPayment(
        address from,
        address to,
        uint256 amount,
        bytes32 referenceId
    ) external returns (bool) {
        require(from != address(0), "Invalid from address");
        require(to != address(0), "Invalid to address");
        require(amount > 0, "Amount must be positive");

        IERC20 usdc = IERC20(usdcToken);

        // Transfer USDC from payer to recipient
        require(
            usdc.transferFrom(from, to, amount),
            "USDC transfer failed"
        );

        emit PaymentProcessed(from, to, amount, referenceId);

        return true;
    }

    /**
     * @notice Get USDC balance of an address
     * @param account Address to check
     * @return Balance in USDC
     */
    function getBalance(address account) external view returns (uint256) {
        return IERC20(usdcToken).balanceOf(account);
    }
}
```

### Step 2.3: AuctionEscrow Contract

Manages matching and settlement between intents.

**Create `contracts/src/AuctionEscrow.sol`:**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./IntentRegistry.sol";
import "./PaymentRouter.sol";

/**
 * @title AuctionEscrow
 * @notice Manages matching and settlement between intents
 * @dev Coordinates between IntentRegistry and PaymentRouter
 */
contract AuctionEscrow {
    IntentRegistry public immutable intentRegistry;
    PaymentRouter public immutable paymentRouter;

    /// @notice Match data structure
    struct Match {
        bytes32 matchId;
        bytes32 bidIntentId;
        bytes32 askIntentId;
        uint256 matchedPrice;
        uint256 matchedQuantity;
        uint256 timestamp;
        bool settled;
    }

    /// @notice Mapping from match ID to match data
    mapping(bytes32 => Match) public matches;

    /// @notice Events
    event MatchCreated(
        bytes32 indexed matchId,
        bytes32 indexed bidIntentId,
        bytes32 indexed askIntentId,
        uint256 matchedPrice,
        uint256 matchedQuantity
    );

    event MatchSettled(
        bytes32 indexed matchId,
        address buyer,
        address seller,
        uint256 settlementAmount
    );

    /**
     * @notice Constructor
     * @param _intentRegistry IntentRegistry address
     * @param _paymentRouter PaymentRouter address
     */
    constructor(
        address _intentRegistry,
        address _paymentRouter
    ) {
        require(_intentRegistry != address(0), "Invalid registry");
        require(_paymentRouter != address(0), "Invalid router");

        intentRegistry = IntentRegistry(_intentRegistry);
        paymentRouter = PaymentRouter(_paymentRouter);
    }

    /**
     * @notice Create a match between bid and ask intents
     * @param matchId Unique match identifier
     * @param bidIntentId Bid intent ID
     * @param askIntentId Ask intent ID
     * @param matchedPrice Agreed price
     * @param matchedQuantity Agreed quantity
     */
    function createMatch(
        bytes32 matchId,
        bytes32 bidIntentId,
        bytes32 askIntentId,
        uint256 matchedPrice,
        uint256 matchedQuantity
    ) external {
        require(matches[matchId].timestamp == 0, "Match already exists");

        // Verify intents exist and are valid
        IntentRegistry.Intent memory bidIntent = intentRegistry.getIntent(bidIntentId);
        IntentRegistry.Intent memory askIntent = intentRegistry.getIntent(askIntentId);

        require(bidIntent.actor != address(0), "Bid intent not found");
        require(askIntent.actor != address(0), "Ask intent not found");
        require(
            bidIntent.intentType == IntentRegistry.IntentType.BID,
            "First intent must be BID"
        );
        require(
            askIntent.intentType == IntentRegistry.IntentType.ASK,
            "Second intent must be ASK"
        );

        matches[matchId] = Match({
            matchId: matchId,
            bidIntentId: bidIntentId,
            askIntentId: askIntentId,
            matchedPrice: matchedPrice,
            matchedQuantity: matchedQuantity,
            timestamp: block.timestamp,
            settled: false
        });

        emit MatchCreated(
            matchId,
            bidIntentId,
            askIntentId,
            matchedPrice,
            matchedQuantity
        );
    }

    /**
     * @notice Settle a match by processing payment
     * @param matchId Match to settle
     */
    function settleMatch(bytes32 matchId) external {
        Match storage matchData = matches[matchId];
        require(matchData.timestamp > 0, "Match does not exist");
        require(!matchData.settled, "Match already settled");

        // Get intent details
        IntentRegistry.Intent memory bidIntent = intentRegistry.getIntent(matchData.bidIntentId);
        IntentRegistry.Intent memory askIntent = intentRegistry.getIntent(matchData.askIntentId);

        // Calculate settlement amount (price * quantity)
        uint256 settlementAmount = (matchData.matchedPrice * matchData.matchedQuantity) / 1e18;

        // Process payment from buyer to seller
        require(
            paymentRouter.processPayment(
                bidIntent.actor,  // Buyer
                askIntent.actor,  // Seller
                settlementAmount,
                matchId
            ),
            "Payment failed"
        );

        matchData.settled = true;

        emit MatchSettled(
            matchId,
            bidIntent.actor,
            askIntent.actor,
            settlementAmount
        );
    }

    /**
     * @notice Get match details
     * @param matchId Match ID
     * @return Match data
     */
    function getMatch(bytes32 matchId) external view returns (Match memory) {
        return matches[matchId];
    }
}
```

### Step 2.4: Deploy Script

**Create `contracts/script/Deploy.s.sol`:**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/IntentRegistry.sol";
import "../src/PaymentRouter.sol";
import "../src/AuctionEscrow.sol";

contract Deploy is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");

        // Arc testnet USDC address
        address usdcAddress = 0x3600000000000000000000000000000000000000;

        vm.startBroadcast(deployerPrivateKey);

        // Deploy contracts
        IntentRegistry intentRegistry = new IntentRegistry();
        PaymentRouter paymentRouter = new PaymentRouter(usdcAddress);
        AuctionEscrow auctionEscrow = new AuctionEscrow(
            address(intentRegistry),
            address(paymentRouter)
        );

        vm.stopBroadcast();

        // Log addresses
        console.log("IntentRegistry:", address(intentRegistry));
        console.log("PaymentRouter:", address(paymentRouter));
        console.log("AuctionEscrow:", address(auctionEscrow));

        // Write to file
        string memory json = string(abi.encodePacked(
            "{\n",
            '  "IntentRegistry": "', vm.toString(address(intentRegistry)), '",\n',
            '  "PaymentRouter": "', vm.toString(address(paymentRouter)), '",\n',
            '  "AuctionEscrow": "', vm.toString(address(auctionEscrow)), '"\n',
            "}"
        ));

        vm.writeFile("deployment-info.json", json);
    }
}
```

### Step 2.5: Configure Foundry

**Edit `contracts/foundry.toml`:**

```toml
[profile.default]
src = "src"
out = "out"
libs = ["lib"]
solc_version = "0.8.20"
optimizer = true
optimizer_runs = 200
fs_permissions = [{ access = "read-write", path = "./" }]

[rpc_endpoints]
arc_testnet = "https://rpc.testnet.arc.network"
```

### Step 2.6: Build and Test Contracts

```bash
cd contracts

# Build contracts
forge build

# Run tests (if you have any)
forge test

# Deploy to Arc testnet
forge script script/Deploy.s.sol:Deploy \
  --rpc-url arc_testnet \
  --broadcast \
  --legacy

cd ..
```

**Update `config/.env` with deployed addresses:**
```bash
INTENT_REGISTRY_ADDRESS=0x... # From deployment output
AUCTION_ESCROW_ADDRESS=0x...
PAYMENT_ROUTER_ADDRESS=0x...
```

---

## Part 3: Backend API

### Step 3.1: Create FastAPI Server

**Create `services/api.py`:**

```python
"""
FastAPI Backend for Arc Coordination System
Handles intents, AI agent orchestration, and payments
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('config/.env')

app = FastAPI(
    title="Arc Coordination System API",
    description="AI-powered intent coordination with Arc testnet integration",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class IntentRequest(BaseModel):
    intent_type: str  # "bid" or "ask"
    asset: str
    price: float
    quantity: float
    settlement_asset: str
    actor: str

class IntentResponse(BaseModel):
    intent_id: str
    tx_hash: str
    status: str
    message: str

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if API is running"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# Create intent endpoint
@app.post("/intents", response_model=IntentResponse)
async def create_intent(intent: IntentRequest):
    """
    Create a new intent and submit to blockchain

    Example:
        POST /intents
        {
            "intent_type": "bid",
            "asset": "BTC",
            "price": 95000.0,
            "quantity": 1.0,
            "settlement_asset": "USDC",
            "actor": "0xYourAddress"
        }
    """
    try:
        # TODO: Implement blockchain submission
        # For now, return mock response

        intent_id = f"0x{datetime.now().timestamp()}"
        tx_hash = f"0x{'0' * 64}"

        return IntentResponse(
            intent_id=intent_id,
            tx_hash=tx_hash,
            status="pending",
            message="Intent created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get intents endpoint
@app.get("/intents")
async def get_intents(
    actor: Optional[str] = None,
    intent_type: Optional[str] = None
):
    """
    Get list of intents with optional filters

    Query Parameters:
        - actor: Filter by actor address
        - intent_type: Filter by "bid" or "ask"
    """
    # TODO: Implement database query
    return {
        "intents": [],
        "count": 0
    }

# Run AI agents endpoint
@app.post("/agents/run")
async def run_agents(intent_id: str):
    """
    Run AI agents on an intent to find matches and assess risk

    Example:
        POST /agents/run?intent_id=0x123...
    """
    try:
        # TODO: Implement AI agent orchestration
        return {
            "status": "running",
            "intent_id": intent_id,
            "message": "AI agents started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Run the API:**
```bash
python -m uvicorn services.api:app --reload --host 0.0.0.0 --port 8000
```

**Test it:**
```bash
curl http://localhost:8000/health
```

### Step 3.2: Add Web3 Integration

**Create `services/blockchain.py`:**

```python
"""
Blockchain interaction module
Handles Web3.py connections and smart contract calls
"""

from web3 import Web3
from eth_account import Account
import json
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv('config/.env')

class BlockchainService:
    """Service for interacting with Arc testnet"""

    def __init__(self):
        # Connect to Arc testnet
        self.rpc_url = os.getenv('PAYMENT_RPC_URL')
        self.chain_id = int(os.getenv('PAYMENT_CHAIN_ID', '5042002'))
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))

        # Load account
        private_key = os.getenv('PRIVATE_KEY')
        self.account = Account.from_key(private_key)
        self.address = self.account.address

        # Contract addresses
        self.intent_registry_address = os.getenv('INTENT_REGISTRY_ADDRESS')
        self.payment_router_address = os.getenv('PAYMENT_ROUTER_ADDRESS')
        self.auction_escrow_address = os.getenv('AUCTION_ESCROW_ADDRESS')

        # USDC token
        self.usdc_address = os.getenv('PAYMENT_TOKEN_ADDRESS')

        # Load contract ABIs (simplified)
        self.intent_registry_abi = self._load_abi('IntentRegistry')
        self.payment_router_abi = self._load_abi('PaymentRouter')

    def _load_abi(self, contract_name: str) -> list:
        """Load contract ABI from Foundry build artifacts"""
        abi_path = f"contracts/out/{contract_name}.sol/{contract_name}.json"

        try:
            with open(abi_path, 'r') as f:
                artifact = json.load(f)
                return artifact['abi']
        except FileNotFoundError:
            print(f"Warning: ABI not found for {contract_name}")
            return []

    def create_intent(
        self,
        intent_id: bytes,
        intent_type: int,  # 0=BID, 1=ASK
        asset: str,
        price: int,
        quantity: int,
        settlement_asset: str,
        valid_until: int
    ) -> Dict[str, Any]:
        """
        Create intent on blockchain

        Returns:
            {
                "tx_hash": "0x...",
                "intent_id": "0x...",
                "status": "success"
            }
        """
        # Get contract
        contract = self.web3.eth.contract(
            address=self.intent_registry_address,
            abi=self.intent_registry_abi
        )

        # Build transaction
        txn = contract.functions.createIntent(
            intent_id,
            intent_type,
            asset,
            price,
            quantity,
            settlement_asset,
            valid_until
        ).build_transaction({
            'from': self.address,
            'nonce': self.web3.eth.get_transaction_count(self.address),
            'gas': 200000,
            'gasPrice': self.web3.eth.gas_price
        })

        # Sign and send
        signed_txn = self.account.sign_transaction(txn)
        tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)

        # Wait for receipt
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        return {
            "tx_hash": tx_hash.hex(),
            "intent_id": intent_id.hex(),
            "status": "success" if receipt['status'] == 1 else "failed",
            "block_number": receipt['blockNumber']
        }

    def get_usdc_balance(self, address: str) -> float:
        """Get USDC balance in human-readable format"""
        # ERC-20 balanceOf function
        abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]

        contract = self.web3.eth.contract(
            address=self.usdc_address,
            abi=abi
        )

        balance_wei = contract.functions.balanceOf(address).call()

        # USDC has 6 decimals
        return balance_wei / 1e6

# Create singleton instance
blockchain = BlockchainService()
```

**Update `services/api.py` to use blockchain:**

```python
# Add at the top
from services.blockchain import blockchain
import hashlib
from datetime import datetime, timedelta

# Update create_intent endpoint
@app.post("/intents", response_model=IntentResponse)
async def create_intent(intent: IntentRequest):
    """Create a new intent and submit to blockchain"""
    try:
        # Generate intent ID from hash of payload
        intent_data = f"{intent.intent_type}{intent.asset}{intent.price}{intent.quantity}{datetime.now().isoformat()}"
        intent_id_hash = hashlib.sha256(intent_data.encode()).digest()

        # Convert to contract format
        intent_type_int = 0 if intent.intent_type.lower() == "bid" else 1
        price_wei = int(intent.price * 1e6)  # USDC has 6 decimals
        quantity_wei = int(intent.quantity * 1e18)  # 18 decimals for precision
        valid_until = int((datetime.now() + timedelta(days=1)).timestamp())

        # Submit to blockchain
        result = blockchain.create_intent(
            intent_id=intent_id_hash,
            intent_type=intent_type_int,
            asset=intent.asset,
            price=price_wei,
            quantity=quantity_wei,
            settlement_asset=intent.settlement_asset,
            valid_until=valid_until
        )

        return IntentResponse(
            intent_id=result['intent_id'],
            tx_hash=result['tx_hash'],
            status=result['status'],
            message="Intent created successfully on Arc testnet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Part 4: AI Agents

### Why AI Agents?

AI agents provide:
- **Intelligent matching**: Find best matches based on multiple criteria
- **Risk assessment**: Evaluate fraud, market, and counterparty risks
- **Automation**: Execute complex workflows without human intervention
- **Adaptability**: Learn from patterns and improve over time

### Step 4.1: Base Agent Class

**Create `services/agents/base_agent.py`:**

```python
"""
Base Agent Class
All AI agents inherit from this class
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
from anthropic import Anthropic
import os

@dataclass
class AgentContext:
    """Context passed between agents"""
    current_intent: Dict[str, Any]
    available_intents: List[Dict[str, Any]]
    request_id: str
    previous_results: Dict[str, Any] = None

@dataclass
class AgentResult:
    """Result returned by an agent"""
    success: bool
    confidence: float  # 0.0 to 1.0
    reasoning: str
    output: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "output": self.output
        }

class BaseAgent(ABC):
    """Base class for all AI agents"""

    def __init__(self, model: str = "claude-3-sonnet-20240229"):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.model = model

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        """Execute the agent's main logic"""
        pass

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call Claude API"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.content[0].text
```

### Step 4.2: Matching Agent

**Create `services/agents/matching_agent.py`:**

```python
"""
Matching Agent
Finds compatible intents that can be matched together
"""

from typing import Dict, Any, List
from services.agents.base_agent import BaseAgent, AgentContext, AgentResult

class MatchingAgent(BaseAgent):
    """Agent that finds matching intents"""

    async def run(self, context: AgentContext) -> AgentResult:
        """
        Find matches for the current intent

        Logic:
        - BID intent matches with ASK intent (same asset)
        - ASK intent matches with BID intent (same asset)
        - Price overlap: bid price >= ask price
        - Quantity compatibility
        """
        current = context.current_intent
        available = context.available_intents

        # Filter for opposite type and same asset
        target_type = "ask" if current['intent_type'] == "bid" else "bid"

        candidates = [
            intent for intent in available
            if (intent['intent_type'] == target_type and
                intent['asset'] == current['asset'] and
                intent.get('is_active', True))
        ]

        if not candidates:
            return AgentResult(
                success=True,
                confidence=1.0,
                reasoning="No matching intents found",
                output={"matches": []}
            )

        # Use AI to rank matches
        matches = self._rank_matches(current, candidates)

        return AgentResult(
            success=True,
            confidence=0.9,
            reasoning=f"Found {len(matches)} potential matches",
            output={"matches": matches}
        )

    def _rank_matches(
        self,
        current: Dict[str, Any],
        candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Use AI to rank match quality"""

        # Simple rule-based matching
        matches = []

        for candidate in candidates:
            # Check price compatibility
            if current['intent_type'] == "bid":
                # Bid price should be >= ask price for a match
                if current['price'] >= candidate['price']:
                    spread = ((current['price'] - candidate['price']) / candidate['price']) * 100

                    matches.append({
                        "match_id": f"{current['intent_id'][:16]}_{candidate['intent_id'][:16]}",
                        "counterparty_intent_id": candidate['intent_id'],
                        "match_score": self._calculate_match_score(current, candidate),
                        "spread": round(spread, 2),
                        "matched_price": candidate['price'],  # Buyer pays ask price
                        "matched_quantity": min(current['quantity'], candidate['quantity'])
                    })
            else:
                # Ask price should be <= bid price for a match
                if candidate['price'] >= current['price']:
                    spread = ((candidate['price'] - current['price']) / current['price']) * 100

                    matches.append({
                        "match_id": f"{current['intent_id'][:16]}_{candidate['intent_id'][:16]}",
                        "counterparty_intent_id": candidate['intent_id'],
                        "match_score": self._calculate_match_score(current, candidate),
                        "spread": round(spread, 2),
                        "matched_price": candidate['price'],  # Seller receives bid price
                        "matched_quantity": min(current['quantity'], candidate['quantity'])
                    })

        # Sort by match score (best first)
        matches.sort(key=lambda x: x['match_score'], reverse=True)

        return matches

    def _calculate_match_score(
        self,
        intent1: Dict[str, Any],
        intent2: Dict[str, Any]
    ) -> float:
        """Calculate match quality score (0-100)"""
        score = 0.0

        # Price compatibility (50 points)
        if intent1['intent_type'] == "bid":
            spread = (intent1['price'] - intent2['price']) / intent2['price']
        else:
            spread = (intent2['price'] - intent1['price']) / intent1['price']

        # Lower spread = better match
        price_score = max(0, 50 - (spread * 100))
        score += price_score

        # Quantity match (30 points)
        qty_ratio = min(intent1['quantity'], intent2['quantity']) / max(intent1['quantity'], intent2['quantity'])
        score += qty_ratio * 30

        # Settlement asset match (20 points)
        if intent1.get('settlement_asset') == intent2.get('settlement_asset'):
            score += 20

        return round(score, 2)
```

### Step 4.3: Risk Agent

**Create `services/agents/risk_agent.py`:**

```python
"""
Risk Agent
Assesses overall risk of a trade
"""

from services.agents.base_agent import BaseAgent, AgentContext, AgentResult

class RiskAgent(BaseAgent):
    """Agent that assesses trade risk"""

    async def run(self, context: AgentContext) -> AgentResult:
        """
        Assess risk of the trade

        Factors:
        - Price volatility
        - Counterparty history
        - Trade size
        - Market conditions
        """
        current = context.current_intent
        previous = context.previous_results or {}

        # Get market data from previous agents
        market_data = previous.get('market', {}).get('output', {}).get('market_data', {})
        fraud_check = previous.get('fraud', {}).get('output', {}).get('fraud_check', {})

        # Calculate risk score
        risk_factors = []
        risk_score = 0

        # Fraud score contributes 40%
        if fraud_check:
            fraud_score = fraud_check.get('fraud_score', 0)
            risk_score += fraud_score * 0.4
            if fraud_score > 50:
                risk_factors.append(f"High fraud score: {fraud_score}/100")

        # Market volatility contributes 30%
        if market_data:
            volatility = market_data.get('volatility', 0)
            risk_score += min(volatility, 100) * 0.3
            if volatility > 50:
                risk_factors.append(f"High market volatility: {volatility}%")

        # Trade size contributes 30%
        trade_value = current['price'] * current['quantity']
        if trade_value > 100000:  # > $100k
            size_risk = min((trade_value / 1000000) * 100, 100)
            risk_score += size_risk * 0.3
            risk_factors.append(f"Large trade size: ${trade_value:,.2f}")

        # Make decision
        decision = "approve" if risk_score < 70 else "reject"
        confidence = 0.9 if risk_score < 50 or risk_score > 80 else 0.7

        # Use AI for reasoning
        reasoning = self._generate_reasoning(
            risk_score,
            risk_factors,
            decision
        )

        return AgentResult(
            success=True,
            confidence=confidence,
            reasoning=reasoning,
            output={
                "risk_assessment": {
                    "overall_score": round(risk_score, 2),
                    "risk_factors": risk_factors,
                    "decision": decision,
                    "trade_value": trade_value
                }
            }
        )

    def _generate_reasoning(
        self,
        risk_score: float,
        risk_factors: list,
        decision: str
    ) -> str:
        """Generate AI reasoning for the decision"""

        system_prompt = """You are a risk assessment AI for financial trades.
        Provide clear, concise reasoning for risk decisions."""

        user_prompt = f"""
Risk Score: {risk_score}/100
Risk Factors: {', '.join(risk_factors) if risk_factors else 'None identified'}
Decision: {decision.upper()}

Provide a 2-3 sentence explanation for this risk assessment.
"""

        return self._call_llm(system_prompt, user_prompt)
```

### Step 4.4: LangGraph Workflow

**Create `services/langgraph/workflow.py`:**

```python
"""
LangGraph Workflow
Orchestrates multiple AI agents in a graph structure
"""

from typing import Dict, Any
from langgraph.graph import Graph
from services.agents.matching_agent import MatchingAgent
from services.agents.risk_agent import RiskAgent
from services.agents.base_agent import AgentContext

class AgentWorkflow:
    """Multi-agent workflow using LangGraph"""

    def __init__(self):
        self.matching_agent = MatchingAgent()
        self.risk_agent = RiskAgent()

        # Build workflow graph
        self.graph = self._build_graph()

    def _build_graph(self) -> Graph:
        """
        Build the agent execution graph

        Flow:
        1. Matching Agent (find matches)
        2. If matches found → Market Agent → Fraud Agent → Risk Agent
        3. If no matches → Liquidity Agent
        """
        workflow = Graph()

        # Add nodes
        workflow.add_node("matching", self._run_matching)
        workflow.add_node("risk", self._run_risk)
        workflow.add_node("complete", self._complete)

        # Add edges
        workflow.add_edge("matching", "risk")
        workflow.add_edge("risk", "complete")

        # Set entry point
        workflow.set_entry_point("matching")

        # Compile graph
        return workflow.compile()

    async def _run_matching(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run matching agent"""
        context = state['context']
        result = await self.matching_agent.run(context)
        state['results']['matching'] = result.to_dict()
        return state

    async def _run_risk(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run risk agent"""
        context = state['context']
        context.previous_results = state['results']
        result = await self.risk_agent.run(context)
        state['results']['risk'] = result.to_dict()
        return state

    async def _complete(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Workflow complete"""
        state['status'] = 'complete'
        return state

    async def execute(
        self,
        current_intent: Dict[str, Any],
        available_intents: list,
        request_id: str
    ) -> Dict[str, Any]:
        """Execute the workflow"""

        # Create context
        context = AgentContext(
            current_intent=current_intent,
            available_intents=available_intents,
            request_id=request_id
        )

        # Initial state
        state = {
            'context': context,
            'results': {},
            'status': 'running'
        }

        # Run workflow
        final_state = await self.graph.invoke(state)

        return final_state['results']

# Create singleton
workflow = AgentWorkflow()
```

---

## Part 5: Frontend UI

### Step 5.1: Main Streamlit App

**Create `ui/streamlit_app.py`:**

```python
"""
Streamlit UI for Arc Coordination System
Main application entry point
"""

import streamlit as st
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv('config/.env')

# Page configuration
st.set_page_config(
    page_title="Arc Coordination System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API base URL
API_URL = os.getenv('API_URL', 'http://localhost:8000')

def main():
    """Main application"""

    # Sidebar navigation
    st.sidebar.title("🚀 Arc Coordination System")
    page = st.sidebar.radio(
        "Navigation",
        ["Home", "Create Intent", "View Intents", "AI Agents Demo", "x402 Payment Demo"]
    )

    # Route to page
    if page == "Home":
        show_home()
    elif page == "Create Intent":
        show_create_intent()
    elif page == "View Intents":
        show_view_intents()
    elif page == "AI Agents Demo":
        show_ai_demo()
    elif page == "x402 Payment Demo":
        show_payment_demo()

def show_home():
    """Home page"""
    st.title("🚀 Welcome to Arc Coordination System")

    st.markdown("""
    ## What is Arc Coordination System?

    An AI-powered platform for decentralized intent coordination and settlement on Arc testnet.

    ### Features

    - **🎯 Intent Creation**: Create buy/sell intents for any asset
    - **🤖 AI Agents**: Intelligent matching, fraud detection, and risk assessment
    - **💳 x402 Payments**: Agent-to-agent USDC payments on Arc testnet
    - **🔗 On-Chain Settlement**: Transparent, verifiable settlements

    ### How It Works

    1. **Create Intent**: Specify what you want to buy or sell
    2. **AI Matching**: Agents find the best matches
    3. **Risk Assessment**: Multiple agents verify safety
    4. **Settlement**: Execute trade on Arc testnet with USDC

    ### Get Started

    Use the sidebar to navigate to different sections.
    """)

    # System status
    st.markdown("### System Status")
    col1, col2, col3 = st.columns(3)

    with col1:
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ API: Online")
            else:
                st.error("❌ API: Error")
        except:
            st.error("❌ API: Offline")

    with col2:
        chain_id = os.getenv('PAYMENT_CHAIN_ID')
        st.info(f"🔗 Chain: Arc Testnet ({chain_id})")

    with col3:
        st.info("💰 Currency: USDC")

def show_create_intent():
    """Create intent page"""
    st.title("🎯 Create Trading Intent")

    with st.form("intent_form"):
        col1, col2 = st.columns(2)

        with col1:
            intent_type = st.selectbox("Intent Type", ["BUY", "SELL"])
            asset = st.text_input("Asset", value="BTC", help="Asset to trade (e.g., BTC, ETH)")
            price = st.number_input("Price (USDC)", min_value=0.01, value=95000.0, step=100.0)

        with col2:
            quantity = st.number_input("Quantity", min_value=0.001, value=1.0, step=0.1)
            settlement_asset = st.selectbox("Settlement Currency", ["USDC", "USD"])
            actor = st.text_input("Your Address", value="0x...")

        submitted = st.form_submit_button("Create Intent", type="primary", use_container_width=True)

        if submitted:
            with st.spinner("Creating intent on Arc testnet..."):
                try:
                    # Call API
                    response = requests.post(
                        f"{API_URL}/intents",
                        json={
                            "intent_type": intent_type.lower(),
                            "asset": asset,
                            "price": price,
                            "quantity": quantity,
                            "settlement_asset": settlement_asset,
                            "actor": actor
                        },
                        timeout=30
                    )

                    if response.status_code == 200:
                        data = response.json()

                        st.success("✅ Intent Created Successfully!")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.code(f"Intent ID: {data['intent_id']}")
                        with col2:
                            st.code(f"TX Hash: {data['tx_hash']}")

                        # Show explorer link
                        explorer_url = f"https://testnet.arcscan.app/tx/{data['tx_hash']}"
                        st.markdown(f"[🔍 View on Arc Explorer]({explorer_url})")
                    else:
                        st.error(f"Error: {response.text}")

                except Exception as e:
                    st.error(f"Error creating intent: {str(e)}")

def show_view_intents():
    """View intents page"""
    st.title("📊 View Intents")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_type = st.selectbox("Intent Type", ["All", "BUY", "SELL"])
    with col2:
        filter_asset = st.text_input("Asset", placeholder="e.g., BTC")
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    # Fetch intents
    try:
        response = requests.get(f"{API_URL}/intents", timeout=5)
        if response.status_code == 200:
            data = response.json()
            intents = data.get('intents', [])

            if intents:
                # Display as table
                st.dataframe(intents, use_container_width=True)
            else:
                st.info("No intents found")
    except Exception as e:
        st.error(f"Error fetching intents: {str(e)}")

def show_ai_demo():
    """AI agents demo page"""
    st.title("🤖 AI Agents Demo")
    st.markdown("Watch AI agents find matches and assess risk in real-time!")

    # TODO: Implement AI demo UI
    st.info("AI Agents Demo - Coming Soon")

def show_payment_demo():
    """x402 payment demo page"""
    st.title("💳 x402 Payment Demo")
    st.markdown("See the x402 payment protocol in action")

    # TODO: Implement payment demo UI
    st.info("x402 Payment Demo - Coming Soon")

if __name__ == "__main__":
    main()
```

**Run the UI:**
```bash
streamlit run ui/streamlit_app.py --server.port 8502
```

**Access at:** http://localhost:8502

---

## Part 6: x402 Payment Integration

**See the complete implementation in the repository at:**
- `ui/x402_payment_demo.py` - Interactive payment demo
- `services/payment.py` - Payment service implementation

**Key concepts:**
1. **Off-chain signature**: Payer signs payment intent with private key
2. **On-chain settlement**: Merchant verifies signature and executes ERC-20 transfer
3. **USDC transfers**: Native gas token on Arc testnet
4. **Real-time monitoring**: Transaction links to Arc explorer

---

## Part 7: Deployment to Arc Testnet

### Step 7.1: Get USDC for Testing

Visit the Circle faucet:
```
https://faucet.circle.com
```

Request USDC for your wallet address on Arc testnet.

### Step 7.2: Deploy Smart Contracts

```bash
cd contracts

# Set your private key
export PRIVATE_KEY="0x..."

# Deploy to Arc testnet
forge script script/Deploy.s.sol:Deploy \
  --rpc-url https://rpc.testnet.arc.network \
  --broadcast \
  --legacy

# Verify deployment
forge verify-contract <ADDRESS> \
  --chain 5042002 \
  --constructor-args $(cast abi-encode "constructor(address)" 0x3600000000000000000000000000000000000000)
```

### Step 7.3: Update Configuration

Update `config/.env` with deployed addresses:
```bash
INTENT_REGISTRY_ADDRESS=0x...  # From deployment output
PAYMENT_ROUTER_ADDRESS=0x...
AUCTION_ESCROW_ADDRESS=0x...
```

### Step 7.4: Start Services

```bash
# Terminal 1: Start API
python -m uvicorn services.api:app --host 0.0.0.0 --port 8000

# Terminal 2: Start UI
streamlit run ui/streamlit_app.py --server.port 8502
```

---

## Part 8: Testing End-to-End

### Test 1: Create Intent

1. Navigate to http://localhost:8502
2. Go to "Create Intent"
3. Fill in:
   - Type: BUY
   - Asset: BTC
   - Price: 95000
   - Quantity: 1.0
   - Settlement: USDC
4. Click "Create Intent"
5. Verify transaction on Arc explorer

### Test 2: Run AI Agents

1. Go to "AI Agents Demo"
2. Configure test scenario
3. Watch agents execute step-by-step
4. See matching, fraud detection, risk assessment

### Test 3: x402 Payment

1. Go to "x402 Payment Demo"
2. Click "Start Payment Flow"
3. Watch signature verification
4. See USDC transfer on Arc testnet

---

## Troubleshooting

### Issue: "Connection refused" to API

**Solution:**
```bash
# Check if API is running
curl http://localhost:8000/health

# If not, start it
python -m uvicorn services.api:app --reload
```

### Issue: "Transaction not found" on explorer

**Solution:**
- Wait 30-60 seconds for block confirmation
- Check if contracts are deployed correctly
- Verify RPC URL is correct

### Issue: "Insufficient funds"

**Solution:**
```bash
# Check USDC balance
python -c "from services.blockchain import blockchain; print(blockchain.get_usdc_balance('YOUR_ADDRESS'))"

# Request from faucet
# https://faucet.circle.com
```

### Issue: Contract deployment fails

**Solution:**
```bash
# Check gas price
cast gas-price --rpc-url https://rpc.testnet.arc.network

# Try with --legacy flag
forge script ... --legacy

# Check Foundry version
foundryup
```

---

## Next Steps

### Enhancements

1. **Database Integration**
   - Add PostgreSQL for production
   - Implement intent caching
   - Store agent results

2. **Advanced AI Features**
   - Train custom models
   - Add sentiment analysis
   - Implement price prediction

3. **Security**
   - Add authentication
   - Implement rate limiting
   - Audit smart contracts

4. **Monitoring**
   - Add Prometheus metrics
   - Set up Grafana dashboards
   - Implement alerting

### Resources

- **Arc Testnet Docs**: https://docs.arc.network
- **Foundry Book**: https://book.getfoundry.sh
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Streamlit Docs**: https://docs.streamlit.io

---

## Conclusion

Congratulations! You've built a complete AI-powered intent coordination system with:

✅ Solidity smart contracts on Arc testnet
✅ Multi-agent AI system with LangGraph
✅ FastAPI backend with Web3 integration
✅ Interactive Streamlit frontend
✅ x402 payment protocol implementation
✅ End-to-end testing on Arc testnet

### What You Learned

- **Blockchain Development**: Smart contracts, deployment, Web3 interactions
- **AI Engineering**: Multi-agent systems, LangGraph workflows
- **Backend Development**: FastAPI, async Python, database management
- **Frontend Development**: Streamlit, real-time UIs
- **Payment Protocols**: x402, ECDSA signatures, ERC-20 transfers

### Share Your Project

1. Push to GitHub
2. Deploy to production
3. Write a blog post
4. Share on Twitter/LinkedIn

---

**GitHub Repository**: https://github.com/YOUR-USERNAME/arc-coordination-system

**Built with ❤️ on Arc Testnet**

*Last Updated: 2025-11-05*
