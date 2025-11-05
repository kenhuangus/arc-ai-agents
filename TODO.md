# Arc Coordination System - Agentic AI TODO

**Last Updated**: 2025-11-05

---

## ✅ COMPLETED (Phase 1: Foundation)

### 1. AI Dependencies
- [x] Installed langgraph (1.0.2)
- [x] Installed anthropic (0.72.0) - Claude Sonnet 4.5
- [x] Installed google-generativeai (0.8.5) - Gemini 2.5 Pro
- [x] Installed langsmith (0.4.41) - Tracing/observability
- [x] Verified all imports working

### 2. Directory Structure
- [x] Created `services/agents/` - Agent implementations
- [x] Created `services/langgraph/` - State and graph management
- [x] Created `services/llm/` - LLM client wrappers

### 3. LLM Client Wrappers
- [x] Created `services/llm/claude_client.py` - Claude Sonnet 4.5 wrapper
  - Synchronous and async completion
  - Tool use support
  - JSON parsing
  - Conversation history
- [x] Created `services/llm/gemini_client.py` - Gemini 2.5 Pro wrapper
  - Long-context support (2M tokens)
  - Conversation with history
  - Token counting
  - Safety settings
- [x] Created `services/llm/router.py` - Intelligent LLM routing
  - Auto-selects model based on task
  - Tool use → Claude
  - Long context → Gemini
  - Fallback handling
  - Cost estimation
- [x] Added API key configuration to `config/.env`

### 4. Base Agent Class
- [x] Created `services/agents/base_agent.py`
  - Abstract base class for all agents
  - LLM integration via router
  - Tool definition and execution
  - Conversation history management
  - AgentContext and AgentResult data classes
- [x] Verified imports and basic functionality

### 5. LangGraph State Schema
- [x] Created `services/langgraph/state.py`
  - CoordinationState TypedDict
  - IntentData dataclass
  - MatchResult dataclass
  - MarketData dataclass
  - State creation and serialization helpers
- [x] Created `services/langgraph/graph.py` (placeholder)
  - CoordinationGraph class stub
  - Ready for graph implementation
- [x] Verified state management working

### 6. First Agent Implementation
- [x] Created `services/agents/matching_agent.py`
  - Finds optimal intent matches
  - AI-powered match scoring
  - Tool definitions:
    - calculate_match_score
    - filter_compatible_intents
  - Handles partial matches and spread calculation
  - Returns structured match results with confidence scores
- [x] Verified agent imports and tool execution

### 7. Integration Test
- [x] Created `test_agentic_system.py`
  - Tests matching agent with sample intents
  - Demonstrates complete workflow
  - Tests state management
  - Shows fallback logic when no API keys

---

## 🚧 IN PROGRESS

### 8. Complete Testing
- [ ] Run integration test with API keys
- [ ] Verify end-to-end AI flow
- [ ] Test tool execution with real LLM calls

---

## 📋 TODO (Phase 2: Complete Multi-Agent System)

### 9. Implement Remaining Agents

#### Market Agent (`services/agents/market_agent.py`)
- [ ] Create market analysis agent
- [ ] Analyze price trends and volatility
- [ ] Assess bid-ask spread
- [ ] Use Gemini for long-context market data analysis
- [ ] Tools:
  - `get_market_price` - Fetch current market price
  - `analyze_liquidity` - Check market liquidity
  - `calculate_volatility` - Historical volatility

#### Risk Agent (`services/agents/risk_agent.py`)
- [ ] Create risk assessment agent
- [ ] Evaluate counterparty risk
- [ ] Check position limits
- [ ] Assess market risk exposure
- [ ] Tools:
  - `check_actor_reputation` - Check actor history
  - `calculate_exposure` - Calculate risk exposure
  - `evaluate_collateral` - Verify collateral

#### Fraud Agent (`services/agents/fraud_agent.py`)
- [ ] Create fraud detection agent
- [ ] Detect suspicious patterns
- [ ] Check for wash trading
- [ ] Verify intent authenticity
- [ ] Tools:
  - `check_pattern_anomaly` - Pattern detection
  - `verify_signature` - Cryptographic verification
  - `check_blacklist` - Check against known bad actors

#### Settlement Agent (`services/agents/settlement_agent.py`)
- [ ] Create settlement coordination agent
- [ ] Plan settlement execution
- [ ] Coordinate with escrow contracts
- [ ] Handle partial settlements
- [ ] Tools:
  - `prepare_settlement` - Prepare settlement transaction
  - `execute_escrow` - Call escrow contract
  - `verify_settlement` - Verify on-chain settlement

#### Liquidity Agent (`services/agents/liquidity_agent.py`)
- [ ] Create market making agent
- [ ] Handle unmatched intents
- [ ] Provide liquidity quotes
- [ ] Dynamic pricing strategy
- [ ] Tools:
  - `calculate_quote` - Generate market maker quote
  - `assess_inventory` - Check liquidity provider inventory
  - `execute_market_make` - Execute market making strategy

---

## 📊 Phase 3: LangGraph Workflow

### 10. Build Complete Graph (`services/langgraph/graph.py`)
- [ ] Define all agent nodes
- [ ] Add entry point (matching_agent)
- [ ] Implement conditional routing:
  ```
  matching_agent →
    if matches found → market_agent (parallel) + fraud_agent (parallel)
    if no matches → liquidity_agent

  market_agent → risk_agent

  risk_agent →
    if low risk → settlement_agent
    if high risk → END with warning

  settlement_agent → END
  liquidity_agent → END
  ```
- [ ] Add checkpointing for state persistence
- [ ] Test graph execution

### 11. Routing Logic
- [ ] Implement `route_after_matching()` function
- [ ] Implement `route_after_risk()` function
- [ ] Add confidence-based routing
- [ ] Handle error states

---

## 🔌 Phase 4: API Integration

### 12. Add AI Endpoints to FastAPI (`services/api.py`)
- [ ] POST `/ai/match` - Find matches for intent using AI
- [ ] POST `/ai/analyze` - Analyze intent with full agent workflow
- [ ] GET `/ai/agents` - List available agents and status
- [ ] GET `/ai/explain/{intent_id}` - Explain intent with AI reasoning
- [ ] POST `/ai/natural-language` - Parse natural language intent

Example endpoint:
```python
@app.post("/ai/match")
async def ai_match_intent(intent_id: str):
    """Use AI agents to find matches for intent"""
    # Fetch intent from database
    # Run matching agent
    # Return AI-powered matches with reasoning
```

### 13. Natural Language Intent Parser
- [ ] Create NLP agent to parse user input
- [ ] Convert "I want to buy 1 BTC at $10,000" → IntentData
- [ ] Handle ambiguous inputs with clarification
- [ ] Support multiple languages

---

## 🎨 Phase 5: UI Integration

### 14. Streamlit AI Features (`ui/`)
- [ ] Add "AI Match" button to intent details page
- [ ] Show AI reasoning and confidence scores
- [ ] Display agent workflow visualization
- [ ] Add natural language intent creation
- [ ] Show real-time agent status

### 15. AI Insights Dashboard
- [ ] Create new page: "🤖 AI Insights"
- [ ] Show agent performance metrics
- [ ] Display confidence trends
- [ ] Show successful match reasons
- [ ] Cost tracking (API usage)

---

## 🔧 Phase 6: Production Readiness

### 16. Configuration
- [ ] Add API keys to production config
- [ ] Set up LangSmith tracing project
- [ ] Configure rate limiting
- [ ] Add caching for LLM responses

### 17. Monitoring & Observability
- [ ] Integrate LangSmith for tracing
- [ ] Add agent performance metrics
- [ ] Track LLM costs per request
- [ ] Monitor agent success rates
- [ ] Alert on high error rates

### 18. Testing
- [ ] Unit tests for each agent
- [ ] Integration tests for full workflow
- [ ] Load testing with multiple concurrent requests
- [ ] Test API key rotation
- [ ] Test fallback scenarios

### 19. Documentation
- [ ] Document agent architecture
- [ ] API endpoint documentation
- [ ] Agent tool reference
- [ ] State schema documentation
- [ ] Deployment guide

---

## 🚀 Phase 7: Advanced Features

### 20. Batch Processing
- [ ] Process multiple intents in parallel
- [ ] Bulk matching optimization
- [ ] Batch settlement coordination

### 21. Learning & Optimization
- [ ] Store agent decisions for training data
- [ ] Analyze successful vs failed matches
- [ ] Tune confidence thresholds
- [ ] Optimize routing logic

### 22. Advanced NLP
- [ ] Support complex multi-step intents
- [ ] Handle conditional intents
- [ ] Parse market orders vs limit orders
- [ ] Support time-based conditions

---

## 📝 IMPORTANT NOTES

### API Keys Required
To enable full AI functionality, add these keys to `config/.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
LANGSMITH_API_KEY=lsv2_pt_...
```

### Current System Status
- ✅ All services running (Anvil, API, Streamlit)
- ✅ Database populated with 11 intents
- ✅ Intent submission working (bug fixed)
- ✅ AI foundation complete
- ⚠️ API keys needed for full AI functionality

### File Structure
```
services/
├── llm/
│   ├── __init__.py
│   ├── claude_client.py      ✅ Claude Sonnet 4.5
│   ├── gemini_client.py      ✅ Gemini 2.5 Pro
│   └── router.py             ✅ Multi-LLM routing
├── agents/
│   ├── __init__.py
│   ├── base_agent.py         ✅ Base class
│   ├── matching_agent.py     ✅ First agent
│   ├── market_agent.py       ⬜ TODO
│   ├── risk_agent.py         ⬜ TODO
│   ├── fraud_agent.py        ⬜ TODO
│   ├── settlement_agent.py   ⬜ TODO
│   └── liquidity_agent.py    ⬜ TODO
├── langgraph/
│   ├── __init__.py
│   ├── state.py              ✅ State schema
│   └── graph.py              ⬜ Graph implementation
├── api.py                    ⬜ Add AI endpoints
└── indexer.py

test_agentic_system.py        ✅ Integration test
```

### Business Value
- **30x ROI** on AI costs at scale
- AI cost: ~$2,800/month
- Revenue: ~$83,430/month
- Natural language as competitive moat
- Network effects from proprietary training data

### Next Session Commands
```bash
# Test the system
python3 test_agentic_system.py

# Start services if needed
pkill -f anvil
pkill -f uvicorn
pkill -f streamlit
./start_all.sh

# Check API keys
cat config/.env | grep API_KEY

# Run specific agent test
python3 -m services.agents.matching_agent
```

---

**END OF TODO** - System ready for Phase 2 implementation
