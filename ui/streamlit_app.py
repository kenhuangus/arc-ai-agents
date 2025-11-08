"""
Arc Coordination System - Professional Streamlit Dashboard
Full-featured UI for decentralized intent coordination
"""
import streamlit as st
import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sdk.arc_sdk import ArcSDK
from dotenv import load_dotenv

# Import AI demo page (enhanced version with step-by-step visualization)
from ui.ai_demo_enhanced import show_ai_agents_demo
from ui.x402_payment_demo import show_x402_payment_demo

load_dotenv("config/.env")

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Arc Coordination System",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Arc Layer-1 Coordination System with AP2 Payments"
    }
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================

st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --success-color: #2ca02c;
        --danger-color: #d62728;
        --warning-color: #ff9800;
    }

    /* Header styling */
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1f77b4 0%, #2ca02c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        padding: 1rem 0;
    }

    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }

    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }

    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.25rem;
    }

    .status-active {
        background-color: #d4edda;
        color: #155724;
    }

    .status-matched {
        background-color: #cce5ff;
        color: #004085;
    }

    .status-pending {
        background-color: #fff3cd;
        color: #856404;
    }

    .status-settled {
        background-color: #d1ecf1;
        color: #0c5460;
    }

    /* Info cards */
    .info-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    .info-card h3 {
        margin-top: 0;
        color: #1f77b4;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }

    /* Forms */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stSelectbox>div>div>select {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem;
    }

    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #1f77b4 0%, #2ca02c 100%);
    }

    /* Data tables */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }

    /* Success/Error messages */
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        color: #155724;
        margin: 1rem 0;
    }

    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 1rem;
        color: #721c24;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_env_var(key: str, default: str = "") -> str:
    """Get environment variable from Streamlit secrets or os.environ"""
    try:
        # Try Streamlit secrets first (for cloud deployment)
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    # Fall back to environment variables (for local)
    return os.getenv(key, default)

@st.cache_resource
def get_sdk():
    """Initialize and cache SDK instance"""
    try:
        # Get configuration
        api_base_url = get_env_var("API_BASE_URL", "http://localhost:8000")
        rpc_url = get_env_var("ARC_TESTNET_RPC_URL", "http://localhost:8545")
        private_key = get_env_var("PRIVATE_KEY", "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80")
        intent_registry = get_env_var("INTENT_REGISTRY_ADDRESS", "0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82")
        auction_escrow = get_env_var("AUCTION_ESCROW_ADDRESS", "0x0B306BF915C4d645ff596e518fAf3F9669b97016")
        payment_router = get_env_var("PAYMENT_ROUTER_ADDRESS", "0x9A676e781A523b5d0C0e43731313A708CB607508")

        # Only initialize if we have required values
        if not all([private_key, intent_registry, auction_escrow, payment_router]):
            st.warning("⚠️ Running in demo mode - SDK not fully configured")
            return None

        return ArcSDK(
            api_base_url=api_base_url,
            rpc_url=rpc_url,
            private_key=private_key,
            intent_registry_address=intent_registry,
            auction_escrow_address=auction_escrow,
            payment_router_address=payment_router
        )
    except Exception as e:
        st.warning(f"⚠️ SDK initialization failed: {str(e)[:100]}... Running in demo mode.")
        return None

def run_async(coro):
    """Run async coroutine"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create new loop if current one is running
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

def format_address(address: str, length: int = 10) -> str:
    """Format Ethereum address"""
    if not address:
        return "N/A"
    return f"{address[:length]}...{address[-4:]}"

def format_timestamp(timestamp: int) -> str:
    """Format Unix timestamp"""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

def get_explorer_url(chain_id: int) -> str:
    """Get block explorer base URL for chain ID"""
    explorers = {
        5042002: "https://testnet.arcscan.app",  # Arc Testnet
        1: "https://etherscan.io",                # Ethereum Mainnet
        137: "https://polygonscan.com",           # Polygon
        42161: "https://arbiscan.io",             # Arbitrum
        8453: "https://basescan.org",             # Base
        31337: None,                              # Anvil (local)
    }
    return explorers.get(chain_id, "https://testnet.arcscan.app")  # Default to Arc testnet

def get_tx_url(tx_hash: str, chain_id: int = None) -> str:
    """Get block explorer URL for transaction"""
    if chain_id is None:
        chain_id = int(get_env_var("PAYMENT_CHAIN_ID", "5042002"))

    base_url = get_explorer_url(chain_id)
    if base_url is None:
        return "#"  # No explorer for local chains
    return f"{base_url}/tx/{tx_hash}"

def get_address_url(address: str, chain_id: int = None) -> str:
    """Get block explorer URL for address/contract"""
    if chain_id is None:
        chain_id = int(get_env_var("PAYMENT_CHAIN_ID", "5042002"))

    base_url = get_explorer_url(chain_id)
    if base_url is None:
        return "#"  # No explorer for local chains
    return f"{base_url}/address/{address}"

def format_hash(hash_str: str) -> str:
    """Format hash"""
    return f"{hash_str[:16]}...{hash_str[-8:]}"

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application"""

    # Header
    st.markdown('<h1 class="main-header">🌐 Arc Coordination System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Decentralized Intent Coordination on Arc Layer-1 with AP2 Payments</p>', unsafe_allow_html=True)

    sdk = get_sdk()

    # Sidebar
    with st.sidebar:
        st.markdown("### 👤 Connected Account")
        # Make account address clickable with explorer link
        if sdk and hasattr(sdk, 'account'):
            chain_id = int(get_env_var('PAYMENT_CHAIN_ID', '5042002'))
            account_link = get_address_url(sdk.account.address, chain_id)
            st.markdown(f"[`{format_address(sdk.account.address, 20)}`]({account_link})")
        else:
            st.markdown("`Demo Mode - No Account Connected`")

        st.markdown("---")
        st.markdown("### 🧭 Navigation")

        page = st.radio(
            "",
            [
                "📊 Dashboard",
                "🤖 AI Agents Demo",
                "➕ Create Intent",
                "📋 My Intents",
                "🔄 Matches",
                "📖 Order Book",
                "💳 Payments",
                "🔐 Mandates",
                "⚙️ System Info"
            ],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Quick stats
        st.markdown("### 📈 Quick Stats")
        try:
            intents = run_async(sdk.list_intents())
            matches = run_async(sdk.list_matches())

            st.metric("Total Intents", len(intents))
            st.metric("Total Matches", len(matches))
            st.metric("Active Intents", len([i for i in intents if i.get('is_active')]))
        except:
            st.warning("Could not load stats")

        st.markdown("---")
        st.markdown("### 🔗 Contract Addresses")

        # Get chain ID for explorer links
        chain_id = int(os.getenv('PAYMENT_CHAIN_ID', '5042002'))

        # Registry contract
        registry_addr = os.getenv('INTENT_REGISTRY_ADDRESS', 'N/A')
        if registry_addr != 'N/A':
            st.markdown(f"Registry: [{format_address(registry_addr, 12)}]({get_address_url(registry_addr, chain_id)})")
        else:
            st.caption(f"Registry: {registry_addr}")

        # Escrow contract
        escrow_addr = os.getenv('AUCTION_ESCROW_ADDRESS', 'N/A')
        if escrow_addr != 'N/A':
            st.markdown(f"Escrow: [{format_address(escrow_addr, 12)}]({get_address_url(escrow_addr, chain_id)})")
        else:
            st.caption(f"Escrow: {escrow_addr}")

        # Router contract
        router_addr = os.getenv('PAYMENT_ROUTER_ADDRESS', 'N/A')
        if router_addr != 'N/A':
            st.markdown(f"Router: [{format_address(router_addr, 12)}]({get_address_url(router_addr, chain_id)})")
        else:
            st.caption(f"Router: {router_addr}")

    # Main content area
    if "Dashboard" in page:
        show_dashboard(sdk)
    elif "AI Agents Demo" in page:
        show_ai_agents_demo(sdk)
    elif "Create Intent" in page:
        show_create_intent(sdk)
    elif "My Intents" in page:
        show_my_intents(sdk)
    elif "Matches" in page:
        show_matches(sdk)
    elif "Order Book" in page:
        show_orderbook(sdk)
    elif "Payments" in page:
        show_payments(sdk)
    elif "Mandates" in page:
        show_mandates(sdk)
    elif "System Info" in page:
        show_system_info(sdk)

# ============================================================================
# PAGE: DASHBOARD
# ============================================================================

def show_dashboard(sdk: ArcSDK):
    """Show main dashboard"""
    st.markdown("## 📊 System Dashboard")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    try:
        with st.spinner("Loading data..."):
            intents = run_async(sdk.list_intents())
            matches = run_async(sdk.list_matches())

            active_intents = [i for i in intents if i.get('is_active', False) and not i.get('is_matched', False)]
            matched_intents = [i for i in intents if i.get('is_matched', False)]
            pending_matches = [m for m in matches if m.get('status') == 'pending']
            settled_matches = [m for m in matches if m.get('status') == 'settled']

        with col1:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <div class="metric-label">Total Intents</div>
                <div class="metric-value">{len(intents)}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <div class="metric-label">Active Intents</div>
                <div class="metric-value">{len(active_intents)}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <div class="metric-label">Total Matches</div>
                <div class="metric-value">{len(matches)}</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                <div class="metric-label">Settled</div>
                <div class="metric-value">{len(settled_matches)}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Charts row
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📊 Intent Status Distribution")
            if intents:
                status_data = pd.DataFrame({
                    'Status': ['Active', 'Matched', 'Inactive'],
                    'Count': [
                        len(active_intents),
                        len(matched_intents),
                        len(intents) - len(active_intents) - len(matched_intents)
                    ]
                })
                fig = px.pie(status_data, values='Count', names='Status',
                           color_discrete_sequence=['#43e97b', '#4facfe', '#f5576c'])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No intent data available")

        with col2:
            st.markdown("### 🔄 Match Status Distribution")
            if matches:
                match_statuses = {}
                for m in matches:
                    status = m.get('status', 'unknown')
                    match_statuses[status] = match_statuses.get(status, 0) + 1

                match_data = pd.DataFrame({
                    'Status': list(match_statuses.keys()),
                    'Count': list(match_statuses.values())
                })
                fig = px.bar(match_data, x='Status', y='Count',
                           color='Status',
                           color_discrete_sequence=['#667eea', '#f093fb', '#43e97b', '#f5576c'])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No match data available")

        st.markdown("---")

        # Recent activity
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📝 Recent Intents")
            if intents:
                recent_intents = sorted(intents, key=lambda x: x.get('timestamp', 0), reverse=True)[:5]
                chain_id = int(os.getenv('PAYMENT_CHAIN_ID', '5042002'))

                for intent in recent_intents:
                    status_class = "status-active" if intent.get('is_active') else "status-matched" if intent.get('is_matched') else ""
                    status_text = "Active" if intent.get('is_active') else "Matched" if intent.get('is_matched') else "Inactive"

                    intent_id = intent.get('intent_id', 'Unknown')
                    actor = intent.get('actor', 'N/A')

                    # Intent ID is just an identifier, not a transaction - don't make it clickable
                    intent_display = format_hash(intent_id)

                    if actor != 'N/A':
                        actor_link = get_address_url(actor, chain_id)
                        actor_display = f'<a href="{actor_link}" target="_blank" style="color: #667eea;">{format_address(actor)}</a>'
                    else:
                        actor_display = format_address(actor)

                    st.markdown(f"""
                    <div class="info-card">
                        <strong>{intent_display}</strong>
                        <span class="status-badge {status_class}">{status_text}</span>
                        <br>
                        <small>Asset: {intent.get('settlement_asset', 'N/A')}</small> •
                        <small>Actor: {actor_display}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No recent intents")

        with col2:
            st.markdown("### 🔄 Recent Matches")
            if matches:
                recent_matches = sorted(matches, key=lambda x: x.get('created_at', 0), reverse=True)[:5]
                chain_id = int(os.getenv('PAYMENT_CHAIN_ID', '5042002'))

                for match in recent_matches:
                    status = match.get('status', 'unknown')
                    status_class = f"status-{status}"

                    match_id = match.get('match_id', 'Unknown')
                    bidder = match.get('bidder', 'N/A')

                    # Create explorer links
                    if match_id != 'Unknown':
                        match_link = get_tx_url(match_id, chain_id)
                        match_display = f'<a href="{match_link}" target="_blank" style="color: inherit; text-decoration: none;">{format_hash(match_id)} 🔗</a>'
                    else:
                        match_display = format_hash(match_id)

                    if bidder != 'N/A':
                        bidder_link = get_address_url(bidder, chain_id)
                        bidder_display = f'<a href="{bidder_link}" target="_blank" style="color: #667eea;">{format_address(bidder)}</a>'
                    else:
                        bidder_display = format_address(bidder)

                    st.markdown(f"""
                    <div class="info-card">
                        <strong>{match_display}</strong>
                        <span class="status-badge {status_class}">{status.upper()}</span>
                        <br>
                        <small>Price: {match.get('match_price', 0)}</small> •
                        <small>Bidder: {bidder_display}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No recent matches")

    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")
        with st.expander("Error Details"):
            st.code(str(e))

# ============================================================================
# PAGE: CREATE INTENT
# ============================================================================

def show_create_intent(sdk: ArcSDK):
    """Show create intent page"""
    st.markdown("## ➕ Create New Intent")

    st.info("💡 **Tip**: Create bid intents to buy and ask intents to sell. The matching engine will automatically pair compatible intents.")

    with st.form("create_intent_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            intent_type = st.selectbox(
                "Intent Type",
                ["bid", "ask"],
                help="Bid = Buy order, Ask = Sell order"
            )

            price = st.number_input(
                "Price (in smallest unit)",
                min_value=1,
                value=10000,
                step=100,
                help="Price per unit in smallest currency denomination"
            )

            quantity = st.number_input(
                "Quantity",
                min_value=1,
                value=100,
                help="Number of units to trade"
            )

        with col2:
            # Payment currency (what you're paying with)
            settlement_asset = st.selectbox(
                "💰 Payment Currency (Paying With)",
                ["USDC", "USD", "ETH", "BTC"],
                help="Currency you will use to pay for the asset"
            )

            # Asset to buy/receive
            target_asset = st.selectbox(
                "🎯 Asset to Buy/Receive",
                ["BTC", "ETH", "USDC", "USD", "SOL", "AVAX", "MATIC", "Other"],
                help="Asset you want to buy or receive in this intent"
            )

            valid_hours = st.number_input(
                "Valid for (hours)",
                min_value=1,
                max_value=168,
                value=24,
                help="How long the intent remains valid"
            )

            mandate_id = st.text_input(
                "AP2 Mandate ID",
                value="0x" + "1" * 64,
                help="Payment authorization credential"
            )

        description = st.text_area(
            "Description",
            value=f"{'Buy' if intent_type == 'bid' else 'Sell'} {quantity} {target_asset} at {price} {settlement_asset} per unit",
            help="Brief description of the intent"
        )

        submitted = st.form_submit_button("🚀 Submit Intent", use_container_width=True)

        if submitted:
            with st.spinner("Submitting intent to blockchain..."):
                try:
                    valid_until = int((datetime.now() + timedelta(hours=valid_hours)).timestamp())

                    result = run_async(sdk.submit_intent(
                        intent_payload={"description": description, "type": intent_type},
                        valid_until=valid_until,
                        ap2_mandate_id=mandate_id,
                        settlement_asset=settlement_asset,
                        constraints={
                            "type": intent_type,
                            "price": price,
                            "quantity": quantity,
                            "target_asset": target_asset,
                            "payment_currency": settlement_asset
                        }
                    ))

                    st.success("✅ Intent submitted successfully!")
                    st.balloons()

                    # Get chain ID for explorer links
                    chain_id = int(os.getenv('PAYMENT_CHAIN_ID', '5042002'))
                    intent_id = result.get('intent_id', 'Unknown')
                    tx_hash = result.get('tx_hash', 'Unknown')

                    # Create explorer links
                    # Intent ID is just an identifier, not a transaction - don't make it clickable
                    if intent_id != 'Unknown':
                        intent_display = f"{intent_id[:32]}..."
                    else:
                        intent_display = "Unknown"

                    # Transaction hash IS the actual on-chain transaction - make it clickable
                    if tx_hash != 'Unknown':
                        tx_link = get_tx_url(tx_hash, chain_id)
                        tx_display = f'<a href="{tx_link}" target="_blank" style="color: #667eea;">{tx_hash} 🔗</a>'
                    else:
                        tx_display = "Unknown"

                    st.markdown(f"""
                    <div class="success-box">
                        <h4>Intent Created</h4>
                        <p><strong>Intent ID:</strong> <code>{intent_display}</code></p>
                        <p><strong>Transaction:</strong> <code>{tx_display}</code></p>
                        <p><strong>Type:</strong> {intent_type.upper()} - {target_asset} with {settlement_asset}</p>
                        <p><strong>Price:</strong> {price} {settlement_asset} per {target_asset}</p>
                        <p><strong>Quantity:</strong> {quantity} {target_asset}</p>
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.markdown(f"""
                    <div class="error-box">
                        <h4>❌ Error Submitting Intent</h4>
                        <p>{str(e)}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.expander("Error Details"):
                        st.code(str(e))

# ============================================================================
# PAGE: MY INTENTS
# ============================================================================

def show_my_intents(sdk: ArcSDK):
    """Show user's intents"""
    st.markdown("## 📋 My Intents")

    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        show_active = st.checkbox("Show Active Only", value=True)
    with col2:
        show_unmatched = st.checkbox("Show Unmatched Only", value=False)
    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()

    try:
        with st.spinner("Loading your intents..."):
            intents = run_async(sdk.list_intents(actor=sdk.account.address))

        if not intents:
            st.info("📭 You haven't submitted any intents yet. Create one above!")
            return

        # Apply filters
        filtered_intents = intents
        if show_active:
            filtered_intents = [i for i in filtered_intents if i.get('is_active')]
        if show_unmatched:
            filtered_intents = [i for i in filtered_intents if not i.get('is_matched')]

        if not filtered_intents:
            st.warning("No intents match the selected filters")
            return

        # Display intents
        for intent in filtered_intents:
            with st.expander(f"🎯 Intent {format_hash(intent.get('intent_id', 'Unknown'))} - {intent.get('settlement_asset', 'N/A')}", expanded=False):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("**Status**")
                    if intent.get('is_active'):
                        st.success("✅ Active")
                    else:
                        st.error("❌ Inactive")

                    if intent.get('is_matched'):
                        st.info("🔄 Matched")
                    else:
                        st.warning("⏳ Unmatched")

                with col2:
                    st.markdown("**Details**")
                    st.write(f"Asset: **{intent.get('settlement_asset', 'N/A')}**")
                    st.write(f"Created: {format_timestamp(intent.get('timestamp', 0))}")
                    st.write(f"Expires: {format_timestamp(intent.get('valid_until', 0))}")

                with col3:
                    st.markdown("**Actions**")
                    if intent.get('is_active') and not intent.get('is_matched'):
                        if st.button("🗑️ Cancel", key=f"cancel_{intent.get('intent_id')}"):
                            try:
                                with st.spinner("Cancelling intent..."):
                                    result = run_async(sdk.cancel_intent(intent.get('intent_id')))
                                st.success("Intent cancelled!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                    else:
                        st.caption("No actions available")

                # Additional info
                st.markdown("---")
                st.caption(f"**Intent ID:** `{intent.get('intent_id', 'Unknown')}`")
                st.caption(f"**Intent Hash:** `{intent.get('intent_hash', 'Unknown')}`")
                st.caption(f"**AP2 Mandate:** `{intent.get('ap2_mandate_id', 'Unknown')[:32]}...`")

        # Summary
        st.markdown("---")
        st.markdown(f"### Summary")
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        with summary_col1:
            st.metric("Total", len(intents))
        with summary_col2:
            st.metric("Active", len([i for i in intents if i.get('is_active')]))
        with summary_col3:
            st.metric("Matched", len([i for i in intents if i.get('is_matched')]))

    except Exception as e:
        st.error(f"Error loading intents: {str(e)}")
        with st.expander("Error Details"):
            st.code(str(e))

# ============================================================================
# PAGE: MATCHES
# ============================================================================

def show_matches(sdk: ArcSDK):
    """Show matches page"""
    st.markdown("## 🔄 Matches")

    # Filters
    col1, col2 = st.columns([3, 1])
    with col1:
        status_filter = st.select_slider(
            "Filter by Status",
            options=["all", "pending", "funded", "settled", "disputed", "cancelled"],
            value="all"
        )
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()

    try:
        with st.spinner("Loading matches..."):
            matches = run_async(sdk.list_matches())

        if not matches:
            st.info("📭 No matches yet. Create intents to get started!")
            return

        # Apply filter
        if status_filter != "all":
            matches = [m for m in matches if m.get('status') == status_filter]

        if not matches:
            st.warning(f"No matches with status '{status_filter}'")
            return

        # Display matches
        for match in matches:
            status = match.get('status', 'unknown')
            status_class = f"status-{status}"

            with st.expander(f"🔄 Match {format_hash(match.get('match_id', 'Unknown'))} - {status.upper()}", expanded=False):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("**Parties**")
                    st.write(f"👤 Bidder: `{format_address(match.get('bidder', 'N/A'))}`")
                    st.write(f"👤 Asker: `{format_address(match.get('asker', 'N/A'))}`")

                with col2:
                    st.markdown("**Details**")
                    st.write(f"💰 Price: **{match.get('match_price', 0)}**")
                    st.write(f"📅 Created: {format_timestamp(match.get('created_at', 0))}")
                    st.write(f"⏰ Settle By: {format_timestamp(match.get('settle_by', 0))}")

                with col3:
                    st.markdown("**Status**")
                    st.markdown(f'<span class="status-badge {status_class}">{status.upper()}</span>', unsafe_allow_html=True)

                    # Action buttons
                    if status == 'pending':
                        if match.get('bidder') == sdk.account.address or match.get('asker') == sdk.account.address:
                            amount = st.number_input(
                                "Fund Amount (wei)",
                                min_value=match.get('match_price', 0),
                                value=match.get('match_price', 0),
                                key=f"fund_amount_{match.get('match_id')}"
                            )
                            if st.button("💵 Fund Escrow", key=f"fund_{match.get('match_id')}"):
                                try:
                                    with st.spinner("Funding escrow..."):
                                        result = run_async(sdk.fund_escrow(match.get('match_id'), amount))
                                    st.success("✅ Escrow funded!")
                                    st.json(result)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                # Additional info
                st.markdown("---")
                st.caption(f"**Match ID:** `{match.get('match_id', 'Unknown')}`")
                st.caption(f"**Bid Intent:** `{match.get('bid_intent_id', 'Unknown')[:32]}...`")
                st.caption(f"**Ask Intent:** `{match.get('ask_intent_id', 'Unknown')[:32]}...`")

        # Summary
        st.markdown("---")
        st.markdown(f"### Match Summary")
        status_counts = {}
        for m in matches:
            status = m.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1

        cols = st.columns(len(status_counts))
        for idx, (status, count) in enumerate(status_counts.items()):
            with cols[idx]:
                st.metric(status.capitalize(), count)

    except Exception as e:
        st.error(f"Error loading matches: {str(e)}")
        with st.expander("Error Details"):
            st.code(str(e))

# ============================================================================
# PAGE: ORDER BOOK
# ============================================================================

def show_orderbook(sdk: ArcSDK):
    """Show order book page"""
    st.markdown("## 📖 Order Book")

    col1, col2 = st.columns([3, 1])
    with col1:
        asset = st.selectbox("Select Asset", ["USD", "ETH", "BTC", "USDC"])
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    try:
        with st.spinner(f"Loading order book for {asset}..."):
            orderbook = run_async(sdk.get_orderbook(asset))

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🟢 Bids (Buy Orders)")
            if orderbook.get('bids'):
                bids_df = pd.DataFrame(orderbook['bids'])
                bids_df.index = range(1, len(bids_df) + 1)
                st.dataframe(bids_df, use_container_width=True)

                # Bid chart
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=bids_df['price'],
                    y=bids_df['quantity'],
                    name='Bids',
                    marker_color='#43e97b'
                ))
                fig.update_layout(title="Bid Depth", xaxis_title="Price", yaxis_title="Quantity")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No bids available")

        with col2:
            st.markdown("### 🔴 Asks (Sell Orders)")
            if orderbook.get('asks'):
                asks_df = pd.DataFrame(orderbook['asks'])
                asks_df.index = range(1, len(asks_df) + 1)
                st.dataframe(asks_df, use_container_width=True)

                # Ask chart
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=asks_df['price'],
                    y=asks_df['quantity'],
                    name='Asks',
                    marker_color='#f5576c'
                ))
                fig.update_layout(title="Ask Depth", xaxis_title="Price", yaxis_title="Quantity")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No asks available")

        # Spread info
        if orderbook.get('spread') is not None:
            st.markdown("---")
            st.markdown("### 📊 Market Spread")
            st.metric("Bid-Ask Spread", f"{orderbook['spread']:,}",
                     help="Difference between lowest ask and highest bid")

            if orderbook.get('bids') and orderbook.get('asks'):
                best_bid = max(b['price'] for b in orderbook['bids'])
                best_ask = min(a['price'] for a in orderbook['asks'])
                spread_pct = ((best_ask - best_bid) / best_bid) * 100
                st.metric("Spread %", f"{spread_pct:.2f}%")

    except Exception as e:
        st.error(f"Error loading order book: {str(e)}")
        with st.expander("Error Details"):
            st.code(str(e))

# ============================================================================
# PAGE: PAYMENTS
# ============================================================================

def show_payments(sdk: ArcSDK):
    """Show payments page"""
    st.markdown("## 💳 Payment Management")

    tab1, tab2, tab3 = st.tabs(["x402 Crypto Payments (Demo)", "Create Payment Intent", "Verify Payment"])

    with tab1:
        show_x402_payment_demo()

    with tab2:
        st.markdown("### Create Stripe Payment Intent")
        with st.form("payment_form"):
            col1, col2 = st.columns(2)

            with col1:
                amount = st.number_input("Amount (smallest unit)", min_value=1, value=10000)
                currency = st.selectbox("Currency", ["usd", "eur", "gbp"])
                payer = st.text_input("Payer Address", value=sdk.account.address)

            with col2:
                payee = st.text_input("Payee Address")
                mandate_id = st.text_input("Mandate ID", value="0x" + "1" * 64)

            if st.form_submit_button("💳 Create Payment Intent", use_container_width=True):
                try:
                    with st.spinner("Creating payment intent..."):
                        result = run_async(sdk.create_payment_intent(
                            amount, currency, payer, payee, mandate_id
                        ))

                    st.success("✅ Payment intent created!")
                    st.json(result)

                    if 'client_secret' in result:
                        st.markdown(f"""
                        <div class="success-box">
                            <h4>Payment Intent Created</h4>
                            <p><strong>ID:</strong> <code>{result.get('payment_intent_id', 'Unknown')}</code></p>
                            <p><strong>Amount:</strong> {result.get('amount', 0)} {result.get('currency', '').upper()}</p>
                            <p><strong>Status:</strong> {result.get('status', 'Unknown').upper()}</p>
                            <p><strong>Client Secret:</strong> <code>{result.get('client_secret', 'Unknown')[:32]}...</code></p>
                        </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")

    with tab3:
        st.markdown("### Verify & Anchor Payment")
        payment_intent_id = st.text_input("Payment Intent ID")

        if st.button("✅ Verify Payment", use_container_width=True):
            if not payment_intent_id:
                st.warning("Please enter a payment intent ID")
            else:
                try:
                    with st.spinner("Verifying payment..."):
                        result = run_async(sdk.verify_payment(payment_intent_id))

                    st.success("✅ Payment verified and anchored on-chain!")
                    st.json(result)

                    st.markdown(f"""
                    <div class="success-box">
                        <h4>Payment Verified</h4>
                        <p><strong>Payment ID:</strong> <code>{result.get('payment_intent_id', 'Unknown')}</code></p>
                        <p><strong>Amount:</strong> {result.get('amount', 0)}</p>
                        <p><strong>Transaction:</strong> <code>{result.get('tx_hash', 'Unknown')}</code></p>
                        <p><strong>Verified:</strong> ✅ {result.get('verified', False)}</p>
                    </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")

# ============================================================================
# PAGE: MANDATES
# ============================================================================

def show_mandates(sdk: ArcSDK):
    """Show mandates page"""
    st.markdown("## 🔐 AP2 Payment Mandates")

    st.info("💡 **AP2 Mandates** are payment authorization credentials that enable secure, verified transactions.")

    with st.form("mandate_form"):
        st.markdown("### Register New Mandate")

        col1, col2 = st.columns(2)

        with col1:
            mandate_id = st.text_input("Mandate ID (32 bytes hex)", value="0x" + "1" * 64)
            issuer = st.text_input("Issuer Address", value=sdk.account.address)
            subject = st.text_input("Subject (Payer) Address")

        with col2:
            scope = st.text_input("Scope", value="payment.create")
            valid_days = st.number_input("Valid for (days)", min_value=1, value=365)

        if st.form_submit_button("🔐 Register Mandate", use_container_width=True):
            try:
                with st.spinner("Registering mandate..."):
                    result = run_async(sdk.register_mandate(
                        mandate_id, issuer, subject, scope, valid_days
                    ))

                st.success("✅ Mandate registered successfully!")
                st.balloons()

                st.markdown(f"""
                <div class="success-box">
                    <h4>Mandate Registered</h4>
                    <p><strong>Mandate ID:</strong> <code>{result.get('mandate_id', 'Unknown')}</code></p>
                    <p><strong>Issuer:</strong> <code>{format_address(result.get('issuer', 'Unknown'))}</code></p>
                    <p><strong>Subject:</strong> <code>{format_address(result.get('subject', 'Unknown'))}</code></p>
                    <p><strong>Scope:</strong> {result.get('scope', 'Unknown')}</p>
                    <p><strong>Valid Until:</strong> {result.get('valid_until', 'Unknown')}</p>
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {e}")

# ============================================================================
# PAGE: SYSTEM INFO
# ============================================================================

def show_system_info(sdk: ArcSDK):
    """Show system information"""
    st.markdown("## ⚙️ System Information")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔗 Network Configuration")
        st.code(f"""
RPC URL: {os.getenv('ARC_TESTNET_RPC_URL', 'Not configured')}
API URL: {os.getenv('API_BASE_URL', 'Not configured')}
Chain ID: 31337 (Anvil Local)
        """)

        st.markdown("### 📝 Contract Addresses")

        # Get chain ID for explorer links
        chain_id = int(os.getenv('PAYMENT_CHAIN_ID', '5042002'))

        # IntentRegistry
        registry_addr = os.getenv('INTENT_REGISTRY_ADDRESS', 'Not deployed')
        if registry_addr != 'Not deployed':
            st.markdown(f"**IntentRegistry:**  \n[`{registry_addr}`]({get_address_url(registry_addr, chain_id)})")
        else:
            st.text("IntentRegistry: Not deployed")

        # AuctionEscrow
        escrow_addr = os.getenv('AUCTION_ESCROW_ADDRESS', 'Not deployed')
        if escrow_addr != 'Not deployed':
            st.markdown(f"**AuctionEscrow:**  \n[`{escrow_addr}`]({get_address_url(escrow_addr, chain_id)})")
        else:
            st.text("AuctionEscrow: Not deployed")

        # PaymentRouter
        router_addr = os.getenv('PAYMENT_ROUTER_ADDRESS', 'Not deployed')
        if router_addr != 'Not deployed':
            st.markdown(f"**PaymentRouter:**  \n[`{router_addr}`]({get_address_url(router_addr, chain_id)})")
        else:
            st.text("PaymentRouter: Not deployed")

    with col2:
        st.markdown("### 👤 Account Information")
        # Make account address clickable with explorer link
        chain_id = int(os.getenv('PAYMENT_CHAIN_ID', '5042002'))
        account_link = get_address_url(sdk.account.address, chain_id)
        st.markdown(f"**Address:**  \n[`{sdk.account.address}`]({account_link})")
        st.text("Balance: Check on blockchain")

        st.markdown("### 🏥 API Health")
        try:
            import httpx
            async def check_health():
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{os.getenv('API_BASE_URL', 'http://localhost:8000')}/health", timeout=5)
                    return response.json()

            health = run_async(check_health())
            st.success("✅ API is healthy")
            st.json(health)
        except:
            st.error("❌ API is not responding")

    st.markdown("---")
    st.markdown("### 📚 Documentation")
    st.markdown("""
    - [Arc Network Docs](https://docs.arc.network)
    - [AP2 Protocol](https://ap2-protocol.org)
    - [GitHub Repository](#)
    """)

# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == "__main__":
    main()
