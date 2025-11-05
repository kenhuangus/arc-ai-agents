"""
Enhanced AI Agents Demo with Step-by-Step Visualization

Shows each agent executing in real-time with visual feedback.
"""

import streamlit as st
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from services.langgraph.state import IntentData
from services.agents.matching_agent import MatchingAgent
from services.agents.market_agent import MarketAgent
from services.agents.fraud_agent import FraudAgent
from services.agents.risk_agent import RiskAgent
from services.agents.settlement_agent import SettlementAgent
from services.agents.liquidity_agent import LiquidityAgent
from services.agents.base_agent import AgentContext


# Agent metadata for visualization
AGENT_INFO = {
    "matching": {
        "name": "Matching Agent",
        "emoji": "🎯",
        "description": "Finding optimal intent matches",
        "color": "#1f77b4"
    },
    "market": {
        "name": "Market Agent",
        "emoji": "📈",
        "description": "Analyzing market conditions",
        "color": "#ff7f0e"
    },
    "fraud": {
        "name": "Fraud Agent",
        "emoji": "🛡️",
        "description": "Detecting suspicious patterns",
        "color": "#2ca02c"
    },
    "risk": {
        "name": "Risk Agent",
        "emoji": "⚠️",
        "description": "Assessing risks",
        "color": "#d62728"
    },
    "settlement": {
        "name": "Settlement Agent",
        "emoji": "💳",
        "description": "Planning settlement execution",
        "color": "#9467bd"
    },
    "liquidity": {
        "name": "Liquidity Agent",
        "emoji": "💧",
        "description": "Providing market liquidity",
        "color": "#8c564b"
    }
}


def show_ai_agents_demo(sdk):
    """Enhanced AI Agents Demo with step-by-step visualization"""

    st.markdown("## 🤖 AI Agents Demo - Step by Step")
    st.markdown("Watch each agent execute in real-time!")

    # Initialize session state
    if 'workflow_running' not in st.session_state:
        st.session_state.workflow_running = False
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
    if 'agent_results' not in st.session_state:
        st.session_state.agent_results = {}
    if 'workflow_path' not in st.session_state:
        st.session_state.workflow_path = []

    # Configuration Section
    with st.expander("🔧 Configure Test Scenario", expanded=not st.session_state.workflow_running):
        col1, col2 = st.columns(2)

        with col1:
            intent_type = st.selectbox("Intent Type", ["bid", "ask"], index=0)
            asset = st.text_input("Asset", "BTC")
            price = st.number_input("Price ($)", value=10100.0, step=100.0)
            quantity = st.number_input("Quantity", value=1.0, step=0.1)

        with col2:
            settlement_asset = st.selectbox(
                "💰 Settlement Asset (Payment Currency)",
                ["USDC", "USD", "ETH", "BTC"],
                index=0,
                help="Currency used for payment settlement on Arc testnet"
            )
            actor = st.text_input("Actor Address", "0xBuyer001")
            add_counterparty = st.checkbox("Add Matching Intent", value=True)

        if add_counterparty:
            st.markdown("#### Counterparty Intent")
            col3, col4 = st.columns(2)
            with col3:
                counter_type = "ask" if intent_type == "bid" else "bid"
                counter_price = st.number_input("Counterparty Price ($)", value=10000.0, step=100.0)
            with col4:
                counter_actor = st.text_input("Counterparty Address", "0xSeller001")
                counter_quantity = st.number_input("Counterparty Quantity", value=1.0, step=0.1)

    # Control Buttons
    col1, col2, col3 = st.columns([1, 1, 3])

    with col1:
        if st.button("▶️ Start", disabled=st.session_state.workflow_running, use_container_width=True, type="primary"):
            st.session_state.workflow_running = True
            st.session_state.current_step = 0
            st.session_state.agent_results = {}
            st.session_state.workflow_path = []

            # Store configuration
            st.session_state.config = {
                'intent_type': intent_type,
                'asset': asset,
                'price': price,
                'quantity': quantity,
                'settlement_asset': settlement_asset,
                'actor': actor,
                'add_counterparty': add_counterparty,
                'counter_type': counter_type if add_counterparty else None,
                'counter_price': counter_price if add_counterparty else None,
                'counter_quantity': counter_quantity if add_counterparty else None,
                'counter_actor': counter_actor if add_counterparty else None
            }
            st.rerun()

    with col2:
        if st.button("⏹️ Stop", disabled=not st.session_state.workflow_running, use_container_width=True):
            st.session_state.workflow_running = False
            st.session_state.current_step = 0
            st.rerun()

    st.markdown("---")

    # Workflow Visualization
    if st.session_state.workflow_running or st.session_state.agent_results:
        show_workflow_progress()

    # Execute current step
    if st.session_state.workflow_running:
        execute_current_step()


def show_workflow_progress():
    """Show visual workflow with agent status"""
    st.markdown("### 🔄 Workflow Progress")

    # Workflow diagram
    workflow_steps = st.session_state.workflow_path if st.session_state.workflow_path else [
        "matching", "market", "fraud", "risk", "settlement"
    ]

    # Create columns for each step
    cols = st.columns(len(workflow_steps))

    for idx, agent_key in enumerate(workflow_steps):
        with cols[idx]:
            info = AGENT_INFO[agent_key]

            # Determine status
            if agent_key in st.session_state.agent_results:
                status = "✅ Complete"
                bg_color = "#d4edda"
            elif idx == st.session_state.current_step:
                status = "🔄 Running"
                bg_color = "#fff3cd"
            else:
                status = "⏳ Pending"
                bg_color = "#f8f9fa"

            # Agent card
            st.markdown(f"""
            <div style="
                padding: 15px;
                border-radius: 10px;
                background-color: {bg_color};
                border: 2px solid {info['color']};
                text-align: center;
                min-height: 120px;
            ">
                <div style="font-size: 32px;">{info['emoji']}</div>
                <div style="font-weight: bold; margin-top: 5px;">{info['name']}</div>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">{info['description']}</div>
                <div style="margin-top: 10px; font-weight: bold; color: {info['color']};">{status}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Show completed agent results
    if st.session_state.agent_results:
        show_agent_results()


def show_agent_results():
    """Display results from completed agents"""
    st.markdown("### 📊 Agent Results")

    for agent_key, result in st.session_state.agent_results.items():
        info = AGENT_INFO[agent_key]

        with st.expander(f"{info['emoji']} {info['name']} - {'✅ Success' if result.get('success') else '❌ Failed'}", expanded=False):
            col1, col2 = st.columns([1, 2])

            with col1:
                st.metric("Status", "Success" if result.get('success') else "Failed")
                st.metric("Confidence", f"{result.get('confidence', 0)*100:.0f}%")

            with col2:
                if result.get('reasoning'):
                    st.markdown("**AI Reasoning:**")
                    st.info(result['reasoning'])

            # Agent-specific output
            if result.get('output'):
                st.markdown("**Output:**")

                if agent_key == "matching":
                    matches = result['output'].get('matches', [])
                    st.write(f"Found {len(matches)} matches")
                    for match in matches[:3]:
                        st.json({
                            'match_id': match.get('match_id', 'N/A')[:16] + '...',
                            'score': match.get('match_score', 0),
                            'spread': f"{match.get('spread', 0)}%"
                        })

                elif agent_key == "market":
                    market_data = result['output'].get('market_data', {})
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Price", f"${market_data.get('current_price', 0):,.2f}")
                    with col_b:
                        st.metric("Volatility", f"{market_data.get('volatility', 0)}%")
                    with col_c:
                        sentiment = market_data.get('market_sentiment', 'neutral')
                        st.metric("Sentiment", sentiment.upper())

                elif agent_key == "risk":
                    risk_assessment = result['output'].get('risk_assessment', {})
                    col_a, col_b = st.columns(2)
                    with col_a:
                        score = risk_assessment.get('overall_score', 0)
                        st.metric("Risk Score", f"{score}/100")
                        st.progress(score / 100)
                    with col_b:
                        decision = risk_assessment.get('decision', 'unknown')
                        st.metric("Decision", decision.upper())

                elif agent_key == "fraud":
                    fraud_check = result['output'].get('fraud_check', {})
                    score = fraud_check.get('fraud_score', 0)
                    st.metric("Fraud Score", f"{score}/100 (lower is safer)")
                    st.progress(1 - (score / 100))
                    decision = fraud_check.get('decision', 'unknown')
                    st.write(f"**Decision:** {decision.upper()}")


def execute_current_step():
    """Execute the current agent step"""

    # Get configuration
    if 'config' not in st.session_state:
        st.error("Configuration not found. Please restart.")
        st.session_state.workflow_running = False
        return

    config = st.session_state.config

    # Create intents
    main_intent = create_intent(
        config['intent_type'], config['asset'], config['price'],
        config['quantity'], config['settlement_asset'], config['actor']
    )

    available_intents = []
    if config.get('add_counterparty') and config.get('counter_type'):
        counter_intent = create_intent(
            config['counter_type'], config['asset'], config['counter_price'],
            config['counter_quantity'], config['settlement_asset'], config['counter_actor']
        )
        available_intents.append(counter_intent)

    # Create context
    context = AgentContext(
        current_intent=main_intent,
        available_intents=available_intents,
        request_id=f"demo-{int(time.time())}",
        previous_results=st.session_state.agent_results
    )

    # Execute based on current step
    step = st.session_state.current_step

    if step == 0:
        # Step 1: Matching Agent
        execute_agent("matching", MatchingAgent(), context)
    elif step == 1:
        # Check if matches found
        matching_result = st.session_state.agent_results.get("matching", {})
        matches = matching_result.get('output', {}).get('matches', [])

        if matches:
            # Has matches → continue with market agent
            st.session_state.workflow_path = ["matching", "market", "fraud", "risk", "settlement"]
            execute_agent("market", MarketAgent(), context)
        else:
            # No matches → go to liquidity agent
            st.session_state.workflow_path = ["matching", "liquidity"]
            execute_agent("liquidity", LiquidityAgent(), context)
            # End workflow after liquidity
            st.session_state.workflow_running = False
            st.success("🎉 Workflow completed - Liquidity provided!")
            time.sleep(2)
            st.rerun()
    elif step == 2:
        # Step 3: Fraud Agent
        execute_agent("fraud", FraudAgent(), context)
    elif step == 3:
        # Step 4: Risk Agent
        execute_agent("risk", RiskAgent(), context)
    elif step == 4:
        # Step 5: Check risk decision
        risk_result = st.session_state.agent_results.get("risk", {})
        decision = risk_result.get('output', {}).get('risk_assessment', {}).get('decision', 'reject')

        if decision == "approve":
            execute_agent("settlement", SettlementAgent(), context)
            # End workflow
            st.session_state.workflow_running = False
            st.success("🎉 Workflow completed - Settlement plan created!")
            time.sleep(2)
            st.rerun()
        else:
            # Risk rejected
            st.session_state.workflow_running = False
            st.warning("⚠️ Workflow stopped - Risk assessment rejected the match")
            time.sleep(2)
            st.rerun()


def execute_agent(agent_key: str, agent, context: AgentContext):
    """Execute a single agent and update UI"""

    info = AGENT_INFO[agent_key]

    # Show status
    with st.spinner(f"{info['emoji']} Executing {info['name']}..."):
        try:
            # Run agent
            result = asyncio.run(agent.run(context))

            # Store result
            st.session_state.agent_results[agent_key] = result.to_dict()

            # Move to next step
            st.session_state.current_step += 1

            # Small delay to show completion
            time.sleep(1)

            # Rerun to show next step
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error in {info['name']}: {str(e)}")
            st.session_state.workflow_running = False


def create_intent(intent_type: str, asset: str, price: float, quantity: float,
                  settlement_asset: str, actor: str) -> IntentData:
    """Helper to create an IntentData object"""
    return IntentData(
        intent_id=f"0x{intent_type.upper()}{int(time.time())}",
        intent_hash=f"0x{intent_type}hash",
        actor=actor,
        intent_type=intent_type,
        price=price,
        quantity=quantity,
        asset=asset,
        settlement_asset=settlement_asset,
        timestamp=int(datetime.now().timestamp()),
        valid_until=int(datetime.now().timestamp()) + 86400,
        ap2_mandate_id=f"0xMandate{int(time.time())}",
        is_active=True
    )


if __name__ == "__main__":
    st.set_page_config(page_title="AI Agents Demo", page_icon="🤖", layout="wide")
    show_ai_agents_demo(None)
