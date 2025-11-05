"""
AI Agents Demo Page for Streamlit UI

Interactive demo of the multi-agent coordination system.
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

from services.langgraph.graph import CoordinationGraph
from services.langgraph.state import IntentData, create_initial_state
from services.agents.base_agent import AgentContext


def show_ai_agents_demo(sdk):
    """Show AI Agents Demo page with interactive controls"""

    st.markdown("## 🤖 AI Agents Demo")
    st.markdown("Watch the multi-agent coordination system in action!")

    # Initialize session state
    if 'workflow_running' not in st.session_state:
        st.session_state.workflow_running = False
    if 'workflow_result' not in st.session_state:
        st.session_state.workflow_result = None
    if 'agent_logs' not in st.session_state:
        st.session_state.agent_logs = []
    if 'current_agent' not in st.session_state:
        st.session_state.current_agent = None

    # Top section: Controls and Status
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown("### 🎮 Controls")

    with col2:
        if st.session_state.workflow_running:
            st.markdown("**Status:** 🟢 **Running**")
        else:
            st.markdown("**Status:** ⚪ **Idle**")

    with col3:
        if st.session_state.current_agent:
            st.markdown(f"**Agent:** {st.session_state.current_agent}")

    st.markdown("---")

    # Configuration Section
    with st.expander("🔧 Configure Test Scenario", expanded=not st.session_state.workflow_running):
        st.markdown("#### Test Intent Parameters")

        col1, col2 = st.columns(2)

        with col1:
            intent_type = st.selectbox("Intent Type", ["bid", "ask"], index=0)
            asset = st.text_input("Asset", "BTC")
            price = st.number_input("Price ($)", value=10100.0, step=100.0)
            quantity = st.number_input("Quantity", value=1.0, step=0.1)

        with col2:
            settlement_asset = st.text_input("Settlement Asset", "USD")
            actor = st.text_input("Actor Address", "0xBuyer001")

            # Add counterparty intent
            add_counterparty = st.checkbox("Add Matching Intent", value=True)

        if add_counterparty:
            st.markdown("#### Counterparty Intent (for matching)")
            col3, col4 = st.columns(2)
            with col3:
                counter_type = "ask" if intent_type == "bid" else "bid"
                st.text_input("Counterparty Type", counter_type, disabled=True)
                counter_price = st.number_input("Counterparty Price ($)", value=10000.0, step=100.0)
            with col4:
                counter_actor = st.text_input("Counterparty Address", "0xSeller001")
                counter_quantity = st.number_input("Counterparty Quantity", value=1.0, step=0.1)

    # Control Buttons
    col1, col2, col3 = st.columns([1, 1, 3])

    with col1:
        if st.button("▶️ Start Workflow", disabled=st.session_state.workflow_running, use_container_width=True, type="primary"):
            st.session_state.workflow_running = True
            st.session_state.agent_logs = []
            st.session_state.workflow_result = None
            st.rerun()

    with col2:
        if st.button("⏹️ Stop", disabled=not st.session_state.workflow_running, use_container_width=True):
            st.session_state.workflow_running = False
            st.session_state.current_agent = None
            st.rerun()

    st.markdown("---")

    # Workflow Execution
    if st.session_state.workflow_running:
        execute_workflow(
            intent_type, asset, price, quantity, settlement_asset, actor,
            add_counterparty, counter_type if add_counterparty else None,
            counter_price if add_counterparty else None,
            counter_quantity if add_counterparty else None,
            counter_actor if add_counterparty else None
        )

    # Display Results
    if st.session_state.workflow_result or st.session_state.agent_logs:
        display_results()


def execute_workflow(
    intent_type: str, asset: str, price: float, quantity: float,
    settlement_asset: str, actor: str, add_counterparty: bool,
    counter_type: Optional[str], counter_price: Optional[float],
    counter_quantity: Optional[float], counter_actor: Optional[str]
):
    """Execute the AI workflow"""

    st.markdown("### 🔄 Workflow Execution")

    # Progress container
    progress_container = st.container()
    logs_container = st.container()

    with progress_container:
        progress_bar = st.progress(0.0)
        status_text = st.empty()

    with logs_container:
        st.markdown("#### 📝 Agent Logs")
        log_area = st.empty()

    # Create test intents
    try:
        # Main intent
        main_intent = IntentData(
            intent_id=f"0x{intent_type.upper()}001",
            intent_hash=f"0x{intent_type}hash",
            actor=actor,
            intent_type=intent_type,
            price=price,
            quantity=quantity,
            asset=asset,
            settlement_asset=settlement_asset,
            timestamp=int(datetime.now().timestamp()),
            valid_until=int(datetime.now().timestamp()) + 86400,
            ap2_mandate_id="0xMandate1",
            is_active=True
        )

        # Counterparty intent (if enabled)
        available_intents = []
        if add_counterparty and counter_type and counter_price and counter_quantity and counter_actor:
            counter_intent = IntentData(
                intent_id=f"0x{counter_type.upper()}001",
                intent_hash=f"0x{counter_type}hash",
                actor=counter_actor,
                intent_type=counter_type,
                price=counter_price,
                quantity=counter_quantity,
                asset=asset,
                settlement_asset=settlement_asset,
                timestamp=int(datetime.now().timestamp()),
                valid_until=int(datetime.now().timestamp()) + 86400,
                ap2_mandate_id="0xMandate2",
                is_active=True
            )
            available_intents.append(counter_intent)

        # Create initial state
        initial_state = create_initial_state(
            input_intent=main_intent,
            available_intents=available_intents,
            request_id=f"demo-{int(time.time())}"
        )

        # Build and run graph
        status_text.markdown("🔧 **Initializing coordination graph...**")
        progress_bar.progress(0.1)

        graph = CoordinationGraph()
        graph.build_graph()

        status_text.markdown("✅ **Graph built successfully**")
        progress_bar.progress(0.2)

        # Add log
        st.session_state.agent_logs.append({
            "timestamp": datetime.now(),
            "agent": "System",
            "message": "Coordination graph initialized with 6 agents",
            "status": "success"
        })

        # Run workflow
        status_text.markdown("🚀 **Starting workflow execution...**")
        progress_bar.progress(0.3)

        # Execute async workflow
        result = asyncio.run(graph.run(initial_state))

        # Update progress based on results
        progress_bar.progress(1.0)
        status_text.markdown("✅ **Workflow completed!**")

        # Store result
        st.session_state.workflow_result = result
        st.session_state.workflow_running = False
        st.session_state.current_agent = "Completed"

        # Add completion log
        st.session_state.agent_logs.append({
            "timestamp": datetime.now(),
            "agent": "System",
            "message": f"Workflow completed with status: {result.get('workflow_status', 'unknown')}",
            "status": "success"
        })

        # Display logs
        display_logs(log_area)

        time.sleep(1)
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error executing workflow: {str(e)}")
        st.session_state.workflow_running = False
        st.session_state.agent_logs.append({
            "timestamp": datetime.now(),
            "agent": "System",
            "message": f"Error: {str(e)}",
            "status": "error"
        })
        display_logs(log_area)


def display_logs(container):
    """Display agent logs"""
    if st.session_state.agent_logs:
        log_text = ""
        for log in st.session_state.agent_logs[-20:]:  # Last 20 logs
            timestamp = log['timestamp'].strftime("%H:%M:%S")
            agent = log['agent']
            message = log['message']
            status = log.get('status', 'info')

            emoji = "✅" if status == "success" else "❌" if status == "error" else "ℹ️"
            log_text += f"`{timestamp}` {emoji} **{agent}**: {message}\n\n"

        container.markdown(log_text)


def display_results():
    """Display workflow results"""
    st.markdown("### 📊 Workflow Results")

    if not st.session_state.workflow_result:
        st.info("No results yet. Start the workflow to see results.")
        return

    result = st.session_state.workflow_result

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Status", result.get('workflow_status', 'unknown').upper())

    with col2:
        matches_count = len(result.get('matches', []))
        st.metric("Matches Found", matches_count)

    with col3:
        messages_count = len(result.get('messages', []))
        st.metric("Agent Messages", messages_count)

    with col4:
        success = result.get('success', False)
        st.metric("Success", "✅" if success else "❌")

    st.markdown("---")

    # Detailed Results Tabs
    tabs = st.tabs(["🎯 Matches", "📈 Market Analysis", "⚠️ Risk Assessment", "🛡️ Fraud Check", "💳 Settlement Plan", "📝 Agent Messages"])

    # Tab 1: Matches
    with tabs[0]:
        st.markdown("#### Intent Matches")
        matches = result.get('matches', [])
        if matches:
            for i, match in enumerate(matches):
                with st.expander(f"Match {i+1}: {match.get('match_id', 'Unknown')[:16]}...", expanded=(i==0)):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Intent A:** `{match.get('intent_a_id', 'N/A')}`")
                        st.markdown(f"**Intent B:** `{match.get('intent_b_id', 'N/A')}`")
                        st.markdown(f"**Score:** {match.get('match_score', 0)}")
                    with col2:
                        st.markdown(f"**Settlement Price:** ${match.get('settlement_price', 0):,.2f}")
                        st.markdown(f"**Quantity:** {match.get('settlement_quantity', 0)}")
                        st.markdown(f"**Spread:** {match.get('spread', 0)}%")

                    if match.get('reasoning'):
                        st.markdown("**AI Reasoning:**")
                        st.info(match['reasoning'])
        else:
            st.info("No matches found. The liquidity agent provided a market maker quote instead.")

    # Tab 2: Market Analysis
    with tabs[1]:
        st.markdown("#### Market Intelligence")
        market_data = result.get('market_data')
        if market_data:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Price", f"${market_data.get('current_price', 0):,.2f}")
                st.metric("Volume 24h", f"${market_data.get('volume_24h', 0):,.0f}")
            with col2:
                st.metric("Volatility", f"{market_data.get('volatility', 0)}%")
                st.metric("Bid-Ask Spread", f"{market_data.get('bid_ask_spread', 0)}%")
            with col3:
                sentiment = market_data.get('market_sentiment', 'neutral')
                sentiment_emoji = "🟢" if sentiment == "bullish" else "🔴" if sentiment == "bearish" else "🟡"
                st.metric("Sentiment", f"{sentiment_emoji} {sentiment.upper()}")
                st.metric("Confidence", f"{market_data.get('confidence', 0)*100:.0f}%")
        else:
            st.info("No market analysis available.")

    # Tab 3: Risk Assessment
    with tabs[2]:
        st.markdown("#### Risk Analysis")
        risk = result.get('risk_assessment')
        if risk:
            # Overall risk score
            risk_score = risk.get('overall_score', 0)
            risk_level = risk.get('risk_level', 'unknown')

            col1, col2 = st.columns([1, 2])
            with col1:
                # Risk gauge
                risk_color = "green" if risk_score > 60 else "orange" if risk_score > 40 else "red"
                st.markdown(f"### Risk Score: {risk_score}/100")
                st.progress(risk_score / 100)
                st.markdown(f"**Level:** {risk_level.upper()}")

            with col2:
                decision = risk.get('decision', 'unknown')
                decision_emoji = "✅" if decision == "approve" else "❌"
                st.markdown(f"### Decision: {decision_emoji} {decision.upper()}")

                if risk.get('reasoning'):
                    st.markdown("**AI Reasoning:**")
                    st.info(risk['reasoning'])

            # Risk factors
            if risk.get('risk_factors'):
                st.markdown("**Risk Factors:**")
                for factor, score in risk['risk_factors'].items():
                    st.markdown(f"- {factor}: {score}/100")
        else:
            st.info("No risk assessment available.")

    # Tab 4: Fraud Check
    with tabs[3]:
        st.markdown("#### Fraud Detection")
        fraud = result.get('fraud_check')
        if fraud:
            fraud_score = fraud.get('fraud_score', 0)
            decision = fraud.get('decision', 'unknown')

            col1, col2 = st.columns(2)
            with col1:
                decision_emoji = "✅" if decision == "approve" else "❌"
                st.markdown(f"### {decision_emoji} {decision.upper()}")
                st.markdown(f"**Fraud Score:** {fraud_score}/100")
                st.progress(fraud_score / 100)

            with col2:
                flags = fraud.get('flags', [])
                if flags:
                    st.markdown("**⚠️ Flags Detected:**")
                    for flag in flags:
                        st.warning(flag)
                else:
                    st.success("No fraud indicators detected")

            if fraud.get('reasoning'):
                st.markdown("**AI Reasoning:**")
                st.info(fraud['reasoning'])
        else:
            st.info("No fraud check available.")

    # Tab 5: Settlement Plan
    with tabs[4]:
        st.markdown("#### Settlement Execution Plan")
        settlement = result.get('settlement_plan')
        if settlement:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Settlement ID:** `{settlement.get('settlement_id', 'N/A')}`")
                st.markdown(f"**Type:** {settlement.get('type', 'N/A')}")
                st.markdown(f"**Estimated Gas:** {settlement.get('estimated_gas', 0):,}")

            with col2:
                st.markdown(f"**Est. Time:** {settlement.get('estimated_time_seconds', 0)}s")
                st.markdown(f"**Parties:** {len(settlement.get('parties', []))}")

            # Execution steps
            if settlement.get('execution_steps'):
                st.markdown("**Execution Steps:**")
                for i, step in enumerate(settlement['execution_steps'], 1):
                    st.markdown(f"{i}. {step}")
        else:
            st.info("No settlement plan available (workflow may have been rejected).")

    # Tab 6: Agent Messages
    with tabs[5]:
        st.markdown("#### Agent Communication Log")
        messages = result.get('messages', [])
        if messages:
            for i, msg in enumerate(messages):
                st.text(f"{i+1}. {msg}")
        else:
            st.info("No agent messages recorded.")


if __name__ == "__main__":
    st.set_page_config(page_title="AI Agents Demo", page_icon="🤖", layout="wide")
    show_ai_agents_demo(None)
