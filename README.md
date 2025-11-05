# Arc AI Agents - Intent Coordination System

A sophisticated multi-agent AI system for coordinating and settling trading intents using LangGraph, Claude Sonnet 4.5, and Gemini 2.5 Pro.

![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🎯 Overview

Arc AI Agents is an advanced intent coordination platform that uses a multi-agent AI architecture to:

- **Match trading intents** between buyers and sellers
- **Analyze market conditions** in real-time
- **Detect fraud** and suspicious patterns
- **Assess risk** across multiple dimensions
- **Plan settlement execution** with blockchain integration
- **Provide liquidity** when no matches are found

The system coordinates 6 specialized AI agents using LangGraph for workflow orchestration, with transparent decision-making powered by Claude Sonnet 4.5 and Gemini 2.5 Pro.

---

## ✨ Features

### 🤖 Multi-Agent Coordination

- **6 Specialized Agents**: Matching, Market, Fraud, Risk, Settlement, Liquidity
- **LangGraph Orchestration**: Type-safe state management and workflow control
- **Conditional Routing**: Different paths based on agent decisions
- **Real-time Execution**: Live agent coordination with visual feedback

### 🎮 Interactive UI Demo

- **Step-by-Step Visualization**: Watch each agent execute live
- **Color-Coded Status**: Green (Complete), Yellow (Running), Gray (Pending)
- **Intermediate Results**: See agent outputs after each step
- **Configuration Controls**: Customize test scenarios interactively
- **Comprehensive Results**: 6-tab interface with detailed analysis

### 🔍 Transparent AI

- **Reasoning Display**: See why agents make each decision
- **Confidence Scores**: Quantified certainty for all outputs
- **Audit Trail**: Complete log of agent communication
- **Explainable Decisions**: Human-readable AI explanations

### 🏗️ Production Architecture

- **FastAPI Backend**: RESTful API for intent management
- **Streamlit UI**: Interactive demo and monitoring dashboard
- **Smart Contract Integration**: Foundry-based settlement contracts
- **Local Blockchain**: Anvil for development and testing
- **Type Safety**: Pydantic models throughout

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js (for Foundry/Anvil)
- API Keys: Anthropic Claude, Google Gemini

### Installation

```bash
# Clone repository
git clone <repository-url>
cd arc-contest

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Foundry (for blockchain)
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### Configuration

Create `config/.env`:

```bash
# LLM API Keys
ANTHROPIC_API_KEY=sk-ant-api03-...
GOOGLE_API_KEY=AIza...

# Optional: Blockchain RPC
ANVIL_RPC_URL=http://localhost:8545
```

### Start Services

```bash
# Terminal 1: Start local blockchain
anvil --port 8545

# Terminal 2: Start FastAPI backend
source venv/bin/activate
python -m uvicorn services.api:app --host 0.0.0.0 --port 8000

# Terminal 3: Start Streamlit UI
source venv/bin/activate
streamlit run ui/streamlit_app.py --server.port 8502
```

### Access

- **Streamlit UI**: http://localhost:8502
- **FastAPI Docs**: http://localhost:8000/docs
- **AI Demo**: http://localhost:8502 → Click "🤖 AI Agents Demo"

---

## 📊 Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                     User Interface                       │
│              (Streamlit - Port 8502)                    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend                        │
│                   (Port 8000)                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │          LangGraph Coordination                  │   │
│  │  ┌──────────────────────────────────────────┐   │   │
│  │  │  🎯 Matching Agent  (Claude Sonnet)     │   │   │
│  │  │  📈 Market Agent    (Gemini 2.5 Pro)    │   │   │
│  │  │  🛡️ Fraud Agent     (Claude Sonnet)     │   │   │
│  │  │  ⚠️ Risk Agent      (Claude Sonnet)     │   │   │
│  │  │  💳 Settlement Agent (Claude Sonnet)    │   │   │
│  │  │  💧 Liquidity Agent (Claude Sonnet)     │   │   │
│  │  └──────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Blockchain Layer                            │
│         (Anvil - Local EVM - Port 8545)                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Settlement Contracts (Foundry/Solidity)         │  │
│  │  - Intent Registry                                │  │
│  │  - Settlement Executor                            │  │
│  │  - AP2 Mandate System                            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Agent Workflow

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 🎯 Matching │──────► No matches? ──► 💧 Liquidity ──► END
│   Agent     │                          Agent
└──────┬──────┘
       │ Matches found
       ▼
┌─────────────┐
│ 📈 Market   │
│   Agent     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 🛡️ Fraud   │
│   Agent     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ ⚠️ Risk    │──────► Risk rejected? ──► END (Stop)
│   Agent     │
└──────┬──────┘
       │ Risk approved
       ▼
┌─────────────┐
│ 💳 Settlement│
│   Agent     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│     END     │
│  (Success)  │
└─────────────┘
```

### Technology Stack

**AI & LLMs:**
- [LangGraph](https://github.com/langchain-ai/langgraph) - Multi-agent orchestration
- [Claude Sonnet 4.5](https://www.anthropic.com/claude) - Tool use & reasoning ($3/$15 per MTok)
- [Gemini 2.5 Pro](https://deepmind.google/technologies/gemini/) - Market analysis ($1.25/$5 per MTok)

**Backend:**
- [FastAPI](https://fastapi.tiangolo.com/) - REST API framework
- [Pydantic](https://docs.pydantic.dev/) - Type validation
- [AsyncIO](https://docs.python.org/3/library/asyncio.html) - Async execution

**Frontend:**
- [Streamlit](https://streamlit.io/) - Interactive UI framework
- Custom visualization components

**Blockchain:**
- [Foundry](https://book.getfoundry.sh/) - Smart contract framework
- [Anvil](https://book.getfoundry.sh/anvil/) - Local Ethereum node
- [Web3.py](https://web3py.readthedocs.io/) - Python blockchain interface

---

## 🎮 Using the AI Demo

### Step 1: Access the Demo

1. Open http://localhost:8502
2. Click **🤖 AI Agents Demo** in the sidebar

### Step 2: Configure Scenario

Expand "Configure Test Scenario":

```
Intent Type: bid or ask
Asset: BTC, ETH, etc.
Price: Your price point ($)
Quantity: Amount to trade
Settlement Asset: USD, USDT, etc.
Actor Address: Wallet address

☑️ Add Matching Intent (optional)
  - Creates counterparty automatically
  - Ensures a match will be found
```

### Step 3: Start Workflow

1. Click **▶️ Start** button
2. Watch agents execute sequentially:
   - 🎯 Matching Agent (yellow) → ✅ Complete (green)
   - 📈 Market Agent (yellow) → ✅ Complete (green)
   - 🛡️ Fraud Agent (yellow) → ✅ Complete (green)
   - ⚠️ Risk Agent (yellow) → ✅ Complete (green)
   - 💳 Settlement Agent (yellow) → ✅ Complete (green)

### Step 4: View Results

Explore the 6 result tabs:

- **🎯 Matches**: Intent matches with scores and spreads
- **📈 Market**: Price, volatility, sentiment analysis
- **⚠️ Risk**: Risk scores and approval decisions
- **🛡️ Fraud**: Fraud detection and flags
- **💳 Settlement**: Execution plan with gas estimates
- **📝 Messages**: Complete agent communication log

**Typical execution time**: 15-25 seconds

See [STEP_BY_STEP_DEMO_GUIDE.md](./STEP_BY_STEP_DEMO_GUIDE.md) for detailed walkthrough.

---

## 📁 Project Structure

```
arc-contest/
├── services/
│   ├── agents/                 # AI Agent implementations
│   │   ├── base_agent.py      # Base agent class
│   │   ├── matching_agent.py  # Intent matching
│   │   ├── market_agent.py    # Market analysis
│   │   ├── fraud_agent.py     # Fraud detection
│   │   ├── risk_agent.py      # Risk assessment
│   │   ├── settlement_agent.py # Settlement planning
│   │   └── liquidity_agent.py # Liquidity provision
│   │
│   ├── langgraph/             # LangGraph coordination
│   │   ├── graph.py           # Workflow graph builder
│   │   ├── state.py           # State definitions
│   │   └── tools.py           # Agent tools
│   │
│   ├── llm/                   # LLM client interfaces
│   │   ├── claude_client.py   # Anthropic Claude
│   │   └── gemini_client.py   # Google Gemini
│   │
│   ├── api.py                 # FastAPI application
│   └── intent_service.py      # Intent business logic
│
├── ui/
│   ├── streamlit_app.py       # Main Streamlit app
│   ├── ai_demo_enhanced.py    # Step-by-step demo
│   └── ai_demo_page.py        # Basic demo (legacy)
│
├── contracts/                  # Solidity smart contracts
│   ├── src/
│   │   ├── IntentRegistry.sol
│   │   ├── SettlementExecutor.sol
│   │   └── AP2Mandate.sol
│   └── test/                  # Contract tests
│
├── config/
│   └── .env                   # API keys (gitignored)
│
├── logs/                      # Application logs
│
├── tests/                     # Python tests
│   ├── test_agents.py
│   └── test_workflow.py
│
├── docs/
│   ├── STEP_BY_STEP_DEMO_GUIDE.md
│   ├── AI_DEMO_UI_GUIDE.md
│   └── SYSTEM_VERIFICATION.md
│
├── .gitignore                 # Git ignore rules
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 🔧 Configuration

### Environment Variables

Create `config/.env`:

```bash
# Required: AI Provider API Keys
ANTHROPIC_API_KEY=sk-ant-api03-...
GOOGLE_API_KEY=AIza...

# Optional: Model Selection
CLAUDE_MODEL=claude-sonnet-4-5-20250929
GEMINI_MODEL=gemini-2.5-pro

# Optional: Blockchain
ANVIL_RPC_URL=http://localhost:8545
CHAIN_ID=31337

# Optional: API Configuration
API_HOST=0.0.0.0
API_PORT=8000
STREAMLIT_PORT=8502

# Optional: Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### Agent Configuration

Agents can be configured in their respective files:

**Matching Agent** (`services/agents/matching_agent.py`):
- Match threshold: 0.7 (minimum compatibility)
- Max spread: 5% (price difference limit)

**Risk Agent** (`services/agents/risk_agent.py`):
- Approval threshold: 40/100
- Risk categories: Market, Counterparty, Liquidity, Operational

**Fraud Agent** (`services/agents/fraud_agent.py`):
- Fraud threshold: 80/100
- Pattern detection: Volume spikes, rapid trading, wash trading

---

## 🧪 Testing

### Run Agent Tests

```bash
# All tests
pytest tests/

# Specific agent
pytest tests/test_agents.py::TestMatchingAgent

# With coverage
pytest --cov=services tests/
```

### Run Workflow Test

```bash
# Test full coordination workflow
python tests/test_workflow.py

# Test with specific scenario
python tests/test_workflow.py --scenario no_match
```

### Manual Testing via API

```bash
# Create test intent
curl -X POST http://localhost:8000/intents \
  -H "Content-Type: application/json" \
  -d '{
    "intent_type": "bid",
    "asset": "BTC",
    "price": 10100.0,
    "quantity": 1.0,
    "actor": "0xTest123"
  }'

# Get workflow results
curl http://localhost:8000/workflow/{request_id}
```

---

## 🎯 API Documentation

### Endpoints

**Create Intent**
```http
POST /intents
Content-Type: application/json

{
  "intent_type": "bid",
  "asset": "BTC",
  "price": 10100.0,
  "quantity": 1.0,
  "settlement_asset": "USD",
  "actor": "0xBuyer001"
}
```

**Get Intent**
```http
GET /intents/{intent_id}
```

**Run Coordination Workflow**
```http
POST /workflow/coordinate/{intent_id}
```

**Get Workflow Results**
```http
GET /workflow/{request_id}
```

**Health Check**
```http
GET /health
```

Full API documentation: http://localhost:8000/docs

---

## 📈 Performance

### Typical Execution Times

| Workflow Path | Duration | Cost (approx) |
|--------------|----------|---------------|
| Full workflow (with match) | 15-25s | $0.10 |
| No match (liquidity only) | 5-9s | $0.03 |

### Agent Performance

| Agent | Avg Duration | Model | Cost |
|-------|-------------|-------|------|
| 🎯 Matching | 3-5s | Claude Sonnet | $0.02 |
| 📈 Market | 2-4s | Gemini 2.5 Pro | $0.01 |
| 🛡️ Fraud | 3-5s | Claude Sonnet | $0.02 |
| ⚠️ Risk | 3-5s | Claude Sonnet | $0.02 |
| 💳 Settlement | 4-6s | Claude Sonnet | $0.03 |
| 💧 Liquidity | 2-4s | Claude Sonnet | $0.02 |

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add type hints to all functions
- Write tests for new features
- Update documentation
- Keep agents modular and focused

---

## 📚 Documentation

- [Step-by-Step Demo Guide](./STEP_BY_STEP_DEMO_GUIDE.md) - Detailed UI demo walkthrough
- [AI Demo UI Guide](./AI_DEMO_UI_GUIDE.md) - UI integration documentation
- [System Verification](./SYSTEM_VERIFICATION.md) - Full system test report
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when running)

---

## 🔍 Troubleshooting

### Issue: API keys not working

**Solution**: Verify keys in `config/.env`:
```bash
cat config/.env | grep API_KEY
```

### Issue: Agents not executing

**Solution**: Check if services are running:
```bash
curl http://localhost:8000/health
curl http://localhost:8502
```

### Issue: Workflow stuck

**Solution**: Check logs:
```bash
tail -f logs/api.log
tail -f logs/app.log
```

### Issue: Import errors

**Solution**: Reinstall dependencies:
```bash
pip install -r requirements.txt --force-reinstall
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [LangChain/LangGraph](https://github.com/langchain-ai/langgraph) - Multi-agent orchestration framework
- [Anthropic](https://www.anthropic.com/) - Claude AI models
- [Google DeepMind](https://deepmind.google/) - Gemini AI models
- [Foundry](https://book.getfoundry.sh/) - Smart contract development

---

## 📧 Contact

For questions or support:
- Create an issue on GitHub
- Check documentation in `/docs`
- Review guides: [STEP_BY_STEP_DEMO_GUIDE.md](./STEP_BY_STEP_DEMO_GUIDE.md)

---

**Built with**: LangGraph • Claude Sonnet 4.5 • Gemini 2.5 Pro • Streamlit • FastAPI • Foundry

**Status**: ✅ Production Ready

**Last Updated**: 2025-01-05

---

## 🎉 Quick Demo

Want to see it in action immediately?

```bash
# Terminal 1: Start Anvil
anvil --port 8545

# Terminal 2: Start API
source venv/bin/activate
python -m uvicorn services.api:app --port 8000

# Terminal 3: Start UI
source venv/bin/activate
streamlit run ui/streamlit_app.py --server.port 8502

# Open browser
open http://localhost:8502

# Click "🤖 AI Agents Demo" → Configure → Start
# Watch the agents coordinate in real-time!
```

**Happy coordinating! 🚀**
