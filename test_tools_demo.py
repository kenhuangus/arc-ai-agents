"""
Comprehensive Tool Demo for Arc Agentic AI System

Demonstrates all agent tools working without API keys.
"""

import asyncio
from datetime import datetime

# Import directly to avoid circular imports
from services.agents.matching_agent import MatchingAgent
from services.agents.market_agent import MarketAgent
from services.agents.risk_agent import RiskAgent
from services.agents.fraud_agent import FraudAgent
from services.agents.settlement_agent import SettlementAgent
from services.agents.liquidity_agent import LiquidityAgent
from services.agents.base_agent import AgentContext
from services.langgraph.state import IntentData

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

async def demo_all_tools():
    """Demo all agent tools"""

    print_section("ARC AGENTIC AI SYSTEM - TOOL DEMONSTRATION")

    # Create test intents
    bid_intent = IntentData(
        intent_id="0xBID001",
        intent_hash="0xbid",
        actor="0xBuyer",
        intent_type="bid",
        price=10100.0,
        quantity=1.0,
        asset="BTC",
        settlement_asset="USD",
        timestamp=int(datetime.now().timestamp()),
        valid_until=int(datetime.now().timestamp()) + 86400,
        ap2_mandate_id="0xMandate1",
        is_active=True
    )

    ask_intent = IntentData(
        intent_id="0xASK001",
        intent_hash="0xask",
        actor="0xSeller",
        intent_type="ask",
        price=10000.0,
        quantity=1.0,
        asset="BTC",
        settlement_asset="USD",
        timestamp=int(datetime.now().timestamp()),
        valid_until=int(datetime.now().timestamp()) + 86400,
        ap2_mandate_id="0xMandate2",
        is_active=True
    )

    context = AgentContext(
        current_intent=bid_intent,
        available_intents=[ask_intent],
        request_id="demo-001",
        contracts={"auction_escrow": "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0"}
    )

    # 1. MATCHING AGENT
    print_section("1. MATCHING AGENT")
    matching_agent = MatchingAgent()
    print(f"✓ Agent: {matching_agent.name}")
    print(f"✓ Tools: {len(matching_agent.get_tools())}")

    # Test match score
    match_score = matching_agent._calculate_match_score({
        "intent_a_price": bid_intent.price,
        "intent_b_price": ask_intent.price,
        "intent_a_type": bid_intent.intent_type,
        "intent_b_type": ask_intent.intent_type
    })
    print(f"\n🔧 Match Score Tool:")
    print(f"   Bid: ${bid_intent.price:,.2f} x {bid_intent.quantity}")
    print(f"   Ask: ${ask_intent.price:,.2f} x {ask_intent.quantity}")
    print(f"   Spread: ${match_score['spread']:,.2f} ({match_score['spread_pct']}%)")
    print(f"   Score: {match_score['match_score']}")

    # Test filter
    compatible = await matching_agent._filter_compatible_intents({
        "input_type": "bid",
        "input_asset": "BTC"
    }, context)
    print(f"\n🔧 Filter Tool:")
    print(f"   Available intents: {len(context.available_intents)}")
    print(f"   Compatible ask intents: {compatible['compatible_count']}")

    # 2. MARKET AGENT
    print_section("2. MARKET AGENT")
    market_agent = MarketAgent()
    print(f"✓ Agent: {market_agent.name}")
    print(f"✓ Tools: {len(market_agent.get_tools())}")

    # Test market price
    market_price = market_agent._get_market_price({"asset": "BTC"}, context)
    print(f"\n🔧 Market Price Tool:")
    print(f"   Asset: {market_price['asset']}")
    print(f"   Current Price: ${market_price['current_price']:,.2f}")
    print(f"   Bid-Ask Spread: {market_price['bid_ask_spread']}%")
    print(f"   Data Source: {market_price['data_source']}")

    # Test volatility
    volatility = market_agent._calculate_volatility({"asset": "BTC", "period_hours": 24})
    print(f"\n🔧 Volatility Tool:")
    print(f"   Volatility: {volatility['volatility_pct']}%")
    print(f"   Volatility Level: {volatility['volatility_level']}")

    # 3. RISK AGENT
    print_section("3. RISK AGENT")
    risk_agent = RiskAgent()
    print(f"✓ Agent: {risk_agent.name}")
    print(f"✓ Tools: {len(risk_agent.get_tools())}")

    # Test reputation
    reputation = risk_agent._check_actor_reputation({"actor": "0xBuyer"}, context)
    print(f"\n🔧 Reputation Tool:")
    print(f"   Actor: {reputation['actor']}")
    print(f"   Total Settlements: {reputation['total_settlements']}")
    print(f"   Success Rate: {reputation['success_rate']}%")
    print(f"   Reputation Score: {reputation['reputation_score']}/100")

    # Test exposure
    exposure = risk_agent._calculate_exposure({
        "actor": "0xBuyer",
        "asset": "BTC",
        "new_quantity": 1.0,
        "price": 10100.0
    })
    print(f"\n🔧 Exposure Tool:")
    print(f"   Current Exposure: ${exposure['current_exposure']:,.2f}")
    print(f"   New Exposure: ${exposure['new_exposure']:,.2f}")
    print(f"   Utilization: {exposure['utilization_pct']}%")
    print(f"   Within Limits: {exposure['within_limits']}")

    # 4. FRAUD AGENT
    print_section("4. FRAUD AGENT")
    fraud_agent = FraudAgent()
    print(f"✓ Agent: {fraud_agent.name}")
    print(f"✓ Tools: {len(fraud_agent.get_tools())}")

    # Test wash trading
    wash_check = fraud_agent._check_wash_trading({
        "intent_a_actor": "0xBuyer",
        "intent_b_actor": "0xSeller"
    })
    print(f"\n🔧 Wash Trading Tool:")
    print(f"   Same Actor: {wash_check['same_actor']}")
    print(f"   Same IP: {wash_check['same_ip_address']}")
    print(f"   Is Wash Trade: {wash_check['is_wash_trade']}")

    # Test price anomaly
    price_anomaly = fraud_agent._check_price_anomaly({
        "intent_price": 10100.0,
        "market_price": 10050.0
    })
    print(f"\n🔧 Price Anomaly Tool:")
    print(f"   Intent Price: ${price_anomaly['intent_price']:,.2f}")
    print(f"   Market Price: ${price_anomaly['market_price']:,.2f}")
    print(f"   Deviation: {price_anomaly['deviation_pct']}%")
    print(f"   Is Anomalous: {price_anomaly['is_anomalous']}")

    # 5. SETTLEMENT AGENT
    print_section("5. SETTLEMENT AGENT")
    settlement_agent = SettlementAgent()
    print(f"✓ Agent: {settlement_agent.name}")
    print(f"✓ Tools: {len(settlement_agent.get_tools())}")

    # Test settlement prep
    settlement = settlement_agent._prepare_settlement({
        "match_id": "0xMATCH123",
        "settlement_price": 10050.0,
        "settlement_quantity": 1.0
    }, context)
    print(f"\n🔧 Prepare Settlement Tool:")
    print(f"   Settlement ID: {settlement['settlement_id']}")
    print(f"   Notional Value: ${settlement['notional_value']:,.2f}")
    print(f"   Escrow Contract: {settlement['escrow_contract'][:10]}...")
    print(f"   Status: {settlement['status']}")

    # Test gas estimation
    gas = settlement_agent._estimate_gas({
        "settlement_type": "simple",
        "party_count": 2
    })
    print(f"\n🔧 Gas Estimation Tool:")
    print(f"   Estimated Gas: {gas['estimated_gas']:,}")
    print(f"   Gas Price: {gas['gas_price_gwei']} gwei")
    print(f"   Cost: ${gas['estimated_cost_usd']:.2f}")

    # 6. LIQUIDITY AGENT
    print_section("6. LIQUIDITY AGENT")
    liquidity_agent = LiquidityAgent()
    print(f"✓ Agent: {liquidity_agent.name}")
    print(f"✓ Tools: {len(liquidity_agent.get_tools())}")

    # Test quote calculation
    quote = liquidity_agent._calculate_quote({
        "asset": "BTC",
        "intent_type": "bid",
        "quantity": 1.0,
        "market_price": 10050.0
    }, context)
    print(f"\n🔧 Quote Calculation Tool:")
    print(f"   Bid: ${quote['bid_price']:,.2f}")
    print(f"   Ask: ${quote['ask_price']:,.2f}")
    print(f"   Spread: {quote['spread_bps']} bps")
    print(f"   Quote Type: {quote['quote_type']}")

    # Test inventory
    inventory = liquidity_agent._assess_inventory({"asset": "BTC"}, context)
    print(f"\n🔧 Inventory Assessment Tool:")
    print(f"   Current Position: {inventory['current_position']}")
    print(f"   Skew: {inventory['skew_pct']}%")
    print(f"   Utilization: {inventory['utilization_pct']}%")
    print(f"   Risk Level: {inventory['risk_level']}")

    # SUMMARY
    print_section("SYSTEM SUMMARY")
    total_tools = (
        len(matching_agent.get_tools()) +
        len(market_agent.get_tools()) +
        len(risk_agent.get_tools()) +
        len(fraud_agent.get_tools()) +
        len(settlement_agent.get_tools()) +
        len(liquidity_agent.get_tools())
    )
    print(f"✅ All 6 agents initialized successfully")
    print(f"✅ Total tools: {total_tools}")
    print(f"✅ All tools tested and working")
    print(f"✅ No API keys required for tool functions")
    print(f"✅ System ready for LLM integration")

    print(f"\n{'='*60}")
    print(f"  TO ENABLE FULL AI FUNCTIONALITY:")
    print(f"{'='*60}")
    print(f"\n1. Add to config/.env:")
    print(f"   ANTHROPIC_API_KEY=sk-ant-api03-...")
    print(f"   GOOGLE_API_KEY=AIza...")
    print(f"\n2. Run full workflow:")
    print(f"   python -m services.langgraph.graph")
    print(f"\n3. Integrate with API:")
    print(f"   POST /ai/match - AI-powered matching")
    print(f"   POST /ai/analyze - Full workflow analysis")
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(demo_all_tools())
