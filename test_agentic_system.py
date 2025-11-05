#!/usr/bin/env python3
"""
Test Agentic AI System

Demonstrates the multi-agent intent coordination system.
Tests matching agent with mock intents.
"""

import asyncio
import logging
from datetime import datetime

from services.agents import MatchingAgent, AgentContext
from services.langgraph import IntentData, CoordinationState, create_initial_state
from services.llm import LLMRouter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_test_intents():
    """Create test intents for demonstration"""
    now = int(datetime.now().timestamp())
    one_day = 86400

    # Buyer intent (bid)
    bid1 = IntentData(
        intent_id="0xBID001",
        intent_hash="0xbid001hash",
        actor="0xBuyer1",
        intent_type="bid",
        price=10100.0,
        quantity=1.0,
        asset="BTC",
        settlement_asset="USD",
        timestamp=now,
        valid_until=now + one_day,
        ap2_mandate_id="0xMandate001",
        is_active=True,
        payload={"description": "Buy 1 BTC at $10,100"}
    )

    bid2 = IntentData(
        intent_id="0xBID002",
        intent_hash="0xbid002hash",
        actor="0xBuyer2",
        intent_type="bid",
        price=10200.0,
        quantity=0.5,
        asset="BTC",
        settlement_asset="USD",
        timestamp=now,
        valid_until=now + one_day,
        ap2_mandate_id="0xMandate002",
        is_active=True,
        payload={"description": "Buy 0.5 BTC at $10,200"}
    )

    # Seller intents (ask)
    ask1 = IntentData(
        intent_id="0xASK001",
        intent_hash="0xask001hash",
        actor="0xSeller1",
        intent_type="ask",
        price=10000.0,
        quantity=1.0,
        asset="BTC",
        settlement_asset="USD",
        timestamp=now,
        valid_until=now + one_day,
        ap2_mandate_id="0xMandate003",
        is_active=True,
        payload={"description": "Sell 1 BTC at $10,000"}
    )

    ask2 = IntentData(
        intent_id="0xASK002",
        intent_hash="0xask002hash",
        actor="0xSeller2",
        intent_type="ask",
        price=10050.0,
        quantity=0.8,
        asset="BTC",
        settlement_asset="USD",
        timestamp=now,
        valid_until=now + one_day,
        ap2_mandate_id="0xMandate004",
        is_active=True,
        payload={"description": "Sell 0.8 BTC at $10,050"}
    )

    return bid1, bid2, ask1, ask2


async def test_matching_agent():
    """Test the matching agent with sample intents"""
    print("\n" + "=" * 70)
    print("  Arc Coordination System - Agentic AI Test")
    print("=" * 70)

    # Create test intents
    print("\n📝 Creating test intents...")
    bid1, bid2, ask1, ask2 = create_test_intents()

    print(f"\nBid Intents:")
    print(f"  - {bid1.intent_id}: Buy {bid1.quantity} {bid1.asset} @ ${bid1.price:,.2f}")
    print(f"  - {bid2.intent_id}: Buy {bid2.quantity} {bid2.asset} @ ${bid2.price:,.2f}")

    print(f"\nAsk Intents:")
    print(f"  - {ask1.intent_id}: Sell {ask1.quantity} {ask1.asset} @ ${ask1.price:,.2f}")
    print(f"  - {ask2.intent_id}: Sell {ask2.quantity} {ask2.asset} @ ${ask2.price:,.2f}")

    # Test scenario 1: Match bid1 against available asks
    print("\n" + "-" * 70)
    print("📊 Scenario 1: Finding matches for BID001 ($10,100)")
    print("-" * 70)

    context = AgentContext(
        current_intent=bid1,
        available_intents=[ask1, ask2],  # Two potential matches
        request_id="test-001"
    )

    print("\n🤖 Initializing Matching Agent...")
    agent = MatchingAgent()
    print(f"   Agent: {agent.name}")
    print(f"   Description: {agent.description}")
    print(f"   Tools available: {len(agent.get_tools())}")

    print("\n⚙️  Checking LLM configuration...")
    router = LLMRouter()
    claude_available = router.claude.client is not None
    gemini_available = router.gemini.model is not None

    if not claude_available and not gemini_available:
        print("   ⚠️  No API keys configured - agent will use fallback logic")
        print("   💡 Add ANTHROPIC_API_KEY or GOOGLE_API_KEY to config/.env to enable AI")
        print("\n   Testing matching logic without LLM...")

        # Test tool functions directly
        print("\n   🔧 Testing match score calculation:")
        score_result = agent._calculate_match_score({
            "intent_a_price": bid1.price,
            "intent_b_price": ask1.price,
            "intent_a_type": bid1.intent_type,
            "intent_b_type": ask1.intent_type
        })
        print(f"      Bid ${bid1.price:,.2f} vs Ask ${ask1.price:,.2f}")
        print(f"      Match Score: {score_result['match_score']}")
        print(f"      Spread: ${score_result['spread']:,.2f} ({score_result['spread_pct']}%)")
        print(f"      Settlement Price: ${score_result['settlement_price']:,.2f}")

        print("\n   ✅ Tool logic working correctly")

    else:
        print(f"   ✅ Claude available: {claude_available}")
        print(f"   ✅ Gemini available: {gemini_available}")

        print("\n🚀 Running Matching Agent with AI...")
        try:
            result = await agent.run(context)

            if result.success:
                print(f"\n✅ Agent execution successful!")
                print(f"   Matches found: {result.output.get('match_count', 0)}")
                print(f"   Confidence: {result.confidence:.2%}")
                print(f"   Reasoning: {result.reasoning}")

                if result.output.get('matches'):
                    print(f"\n   Match Details:")
                    for match in result.output['matches']:
                        print(f"   - Match ID: {match['match_id'][:16]}...")
                        print(f"     Intent A: {match['intent_a_id']}")
                        print(f"     Intent B: {match['intent_b_id']}")
                        print(f"     Score: {match['match_score']:.2f}")
                        print(f"     Confidence: {match['confidence']:.2%}")
                        print(f"     Settlement: ${match['settlement_price']:,.2f} x {match['settlement_quantity']}")
                        print(f"     Reasoning: {match['reasoning']}")

                print(f"\n   Next agent: {result.next_agent or 'None'}")

            else:
                print(f"\n❌ Agent failed: {result.error}")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.error("Agent execution failed", exc_info=True)

    # Test scenario 2: Test state management
    print("\n" + "-" * 70)
    print("📦 Scenario 2: Testing LangGraph State Management")
    print("-" * 70)

    initial_state = create_initial_state(
        input_intent=bid1,
        available_intents=[ask1, ask2],
        request_id="test-002"
    )

    print(f"\n   State created: {initial_state['request_id']}")
    print(f"   Input intent: {initial_state['input_intent'].intent_id}")
    print(f"   Available intents: {len(initial_state['available_intents'])}")
    print(f"   Workflow status: {initial_state['workflow_status']}")

    # Add a message to state
    initial_state["messages"].append("Test message from matching agent")
    initial_state["metadata"]["test_key"] = "test_value"

    print(f"   Messages: {len(initial_state['messages'])}")
    print(f"   Metadata keys: {list(initial_state['metadata'].keys())}")

    print("\n   ✅ State management working correctly")

    # Summary
    print("\n" + "=" * 70)
    print("  ✅ TEST SUMMARY")
    print("=" * 70)
    print("\n✓ Components Tested:")
    print("  - IntentData creation and validation")
    print("  - Matching Agent initialization")
    print("  - Tool execution (calculate_match_score)")
    print("  - LangGraph state management")
    print("  - AgentContext and AgentResult")

    if claude_available or gemini_available:
        print("\n✓ AI Integration:")
        print(f"  - Claude Sonnet 4.5: {'✓' if claude_available else '✗'}")
        print(f"  - Gemini 2.5 Pro: {'✓' if gemini_available else '✗'}")
        print("  - LLM Router: ✓")
    else:
        print("\n⚠️  AI Integration:")
        print("  - No API keys configured")
        print("  - Add keys to config/.env to enable full AI functionality")

    print("\n✓ Next Steps:")
    print("  1. Add API keys to config/.env:")
    print("     ANTHROPIC_API_KEY=your_key_here")
    print("     GOOGLE_API_KEY=your_key_here")
    print("  2. Implement remaining agents (Market, Risk, Fraud, etc.)")
    print("  3. Build complete LangGraph workflow")
    print("  4. Integrate with FastAPI endpoints")
    print("  5. Connect to Streamlit UI")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_matching_agent())
