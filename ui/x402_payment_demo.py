"""
x402 Payment Protocol Demo UI Component

Interactive step-by-step visualization of the x402 payment flow
for cryptocurrency payments between agents.
"""

import streamlit as st
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.payment import X402PaymentService
from eth_account import Account
from eth_account.messages import encode_defunct

# Test accounts (works on both Anvil and Arc testnet)
MERCHANT_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
MERCHANT_ADDRESS = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"

PAYER_PRIVATE_KEY = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
PAYER_ADDRESS = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"

# Load network configuration from environment
from dotenv import load_dotenv
load_dotenv('config/.env')

# Arc testnet configuration (default)
ARC_TESTNET_RPC_URL = os.getenv('PAYMENT_RPC_URL', 'https://rpc.testnet.arc.network')
ARC_TESTNET_CHAIN_ID = int(os.getenv('PAYMENT_CHAIN_ID', '5042002'))

# Fallback for local Anvil testing
ANVIL_RPC_URL = "http://localhost:8545"
ANVIL_CHAIN_ID = 31337


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


def get_tx_url(tx_hash: str, chain_id: int) -> str:
    """Get block explorer URL for transaction"""
    base_url = get_explorer_url(chain_id)
    if base_url is None:
        return "#"  # No explorer for local chains
    return f"{base_url}/tx/{tx_hash}"


def init_payment_service() -> Optional[X402PaymentService]:
    """Initialize payment service from environment configuration"""
    try:
        # Use environment configuration (defaults to Arc testnet with USDC)
        service = X402PaymentService.from_env()

        # Override merchant private key for demo
        service.account = Account.from_key(MERCHANT_PRIVATE_KEY)
        service.address = service.account.address

        return service
    except Exception as e:
        st.error(f"Failed to initialize payment service: {e}")
        st.info("Check your .env configuration for PAYMENT_RPC_URL and PAYMENT_CHAIN_ID")
        return None


def show_x402_payment_demo():
    """Show interactive x402 payment protocol demo"""

    st.markdown("## 🔐 x402 Payment Protocol Demo")
    st.markdown("""
    This demo shows the complete x402 payment flow using Arc testnet with USDC payments.
    Watch each step of the cryptocurrency payment process from request to settlement.
    """)

    # Initialize session state
    if 'payment_step' not in st.session_state:
        st.session_state.payment_step = 0
    if 'payment_request' not in st.session_state:
        st.session_state.payment_request = None
    if 'payment_submission' not in st.session_state:
        st.session_state.payment_submission = None
    if 'tx_hash' not in st.session_state:
        st.session_state.tx_hash = None
    if 'payment_result' not in st.session_state:
        st.session_state.payment_result = None
    if 'payment_amount' not in st.session_state:
        st.session_state.payment_amount = 10.0  # 10 USDC default

    # Initialize service
    service = init_payment_service()
    if not service:
        return

    # Display connection status
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔗 Blockchain", "Connected" if service.web3.is_connected() else "Disconnected")
    with col2:
        network_name = "Arc Testnet" if service.chain_id == 5042002 else f"Chain {service.chain_id}"
        st.metric("🌐 Network", f"{network_name} ({service.chain_id})")
    with col3:
        try:
            balance = service.get_balance()
            currency = service.token_symbol if hasattr(service, 'token_symbol') else "ETH"
            st.metric("💰 Merchant Balance", f"{float(balance):.2f} {currency}")
        except:
            st.metric("💰 Merchant Balance", "Error")

    st.markdown("---")

    # Payment configuration
    with st.expander("⚙️ Payment Configuration", expanded=st.session_state.payment_step == 0):
        col1, col2 = st.columns(2)

        with col1:
            currency = service.token_symbol if hasattr(service, 'token_symbol') else "ETH"
            min_amt = float(os.getenv('MIN_PAYMENT_AMOUNT', '1.0')) if currency == "USDC" else 0.001
            max_amt = float(os.getenv('MAX_PAYMENT_AMOUNT', '10000.0')) if currency == "USDC" else 10.0
            step_amt = 1.0 if currency == "USDC" else 0.001

            amount = st.number_input(
                f"Payment Amount ({currency})",
                min_value=min_amt,
                max_value=max_amt,
                value=st.session_state.payment_amount,
                step=step_amt,
                format="%.2f" if currency == "USDC" else "%.4f"
            )
            service_id = st.text_input("Service ID", value=f"settlement_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        with col2:
            description = st.text_area(
                "Description",
                value="Payment for Arc Settlement Service",
                height=100
            )

        if st.button("🚀 Start Payment Flow", type="primary", use_container_width=True):
            st.session_state.payment_amount = amount
            st.session_state.payment_step = 1
            st.session_state.payment_request = None
            st.session_state.payment_submission = None
            st.session_state.tx_hash = None
            st.session_state.payment_result = None
            st.rerun()

    st.markdown("---")

    # Progress indicator
    progress = st.session_state.payment_step / 7
    st.progress(progress)

    step_names = [
        "Configuration",
        "Payment Request",
        "Signature",
        "Verification",
        "Transaction Prep",
        "On-Chain Payment",
        "Verification Complete"
    ]

    if st.session_state.payment_step < len(step_names):
        st.markdown(f"### Current Step: **{step_names[st.session_state.payment_step]}**")

    st.markdown("---")

    # Step-by-step flow

    # ========================================================================
    # STEP 1: Create Payment Request (402 Payment Required)
    # ========================================================================
    if st.session_state.payment_step >= 1:
        with st.container():
            st.markdown("### 1️⃣ Payment Request Created (402 Payment Required)")

            if st.session_state.payment_request is None:
                with st.spinner("Merchant creating payment request..."):
                    try:
                        payment_request = service.create_payment_request(
                            amount_eth=st.session_state.payment_amount,
                            service_id=service_id if 'service_id' in locals() else "settlement_demo",
                            description=description if 'description' in locals() else "Demo payment",
                            metadata={"demo": True, "timestamp": datetime.now().isoformat()}
                        )
                        st.session_state.payment_request = payment_request
                    except Exception as e:
                        st.error(f"Error creating payment request: {e}")
                        return

            col1, col2 = st.columns([2, 1])

            with col1:
                st.success("✅ Merchant sent HTTP 402 Payment Required")
                st.json(st.session_state.payment_request)

            with col2:
                currency = service.token_symbol if hasattr(service, 'token_symbol') else "ETH"
                st.info(f"""
                **Merchant Details**

                Address: `{MERCHANT_ADDRESS[:10]}...`

                Requesting: **{st.session_state.payment_amount} {currency}**

                Currency: **{currency}**

                Chain: **{service.chain_id}**
                """)

            if st.session_state.payment_step == 1:
                if st.button("➡️ Continue to Signature", type="primary"):
                    st.session_state.payment_step = 2
                    st.rerun()

        st.markdown("---")

    # ========================================================================
    # STEP 2: Payer Signs Payment Intent
    # ========================================================================
    if st.session_state.payment_step >= 2:
        with st.container():
            st.markdown("### 2️⃣ Payer Signs Payment Intent (Off-Chain)")

            if st.session_state.payment_submission is None:
                with st.spinner("Payer signing payment intent..."):
                    try:
                        # Payer signs the payment
                        payer_account = Account.from_key(PAYER_PRIVATE_KEY)
                        payment_data = st.session_state.payment_request['payment']

                        # Create message to sign
                        message_text = json.dumps(payment_data, sort_keys=True)
                        message = encode_defunct(text=message_text)

                        # Sign message
                        signed_message = payer_account.sign_message(message)
                        signature = signed_message.signature.hex()

                        # Create payment submission
                        payment_submission = {
                            "type": "payment-submitted",
                            "version": "0.1",
                            "timestamp": datetime.now().isoformat(),
                            "payment": payment_data,
                            "signature": signature,
                            "payer": {
                                "address": payer_account.address,
                                "type": "ethereum"
                            }
                        }

                        st.session_state.payment_submission = payment_submission
                    except Exception as e:
                        st.error(f"Error signing payment: {e}")
                        return

            col1, col2 = st.columns([2, 1])

            with col1:
                st.success("✅ Payer signed payment with private key")
                st.json(st.session_state.payment_submission)

            with col2:
                st.info(f"""
                **Payer Details**

                Address: `{PAYER_ADDRESS[:10]}...`

                Signature: `{st.session_state.payment_submission['signature'][:20]}...`

                Method: **ECDSA**
                """)

            if st.session_state.payment_step == 2:
                if st.button("➡️ Continue to Verification", type="primary"):
                    st.session_state.payment_step = 3
                    st.rerun()

        st.markdown("---")

    # ========================================================================
    # STEP 3: Merchant Verifies Signature
    # ========================================================================
    if st.session_state.payment_step >= 3:
        with st.container():
            st.markdown("### 3️⃣ Merchant Verifies Signature")

            with st.spinner("Verifying cryptographic signature..."):
                try:
                    is_valid = service.verify_payment_signature(st.session_state.payment_submission)
                except Exception as e:
                    st.error(f"Error verifying signature: {e}")
                    return

            col1, col2 = st.columns([2, 1])

            with col1:
                if is_valid:
                    st.success("✅ Signature verified successfully!")
                    st.write("The signature matches the payer's address. Payment intent is authentic.")
                else:
                    st.error("❌ Signature verification failed")
                    st.write("The signature does not match the payer's address.")
                    return

            with col2:
                st.info(f"""
                **Verification**

                Signer: `{PAYER_ADDRESS[:10]}...`

                Recipient: `{MERCHANT_ADDRESS[:10]}...`

                Status: **Valid ✓**
                """)

            if st.session_state.payment_step == 3:
                if st.button("➡️ Prepare Transaction", type="primary"):
                    st.session_state.payment_step = 4
                    st.rerun()

        st.markdown("---")

    # ========================================================================
    # STEP 4: Prepare Transaction Parameters
    # ========================================================================
    if st.session_state.payment_step >= 4:
        with st.container():
            st.markdown("### 4️⃣ Merchant Prepares Transaction Parameters")

            with st.spinner("Preparing transaction for blockchain..."):
                try:
                    tx_prepared = service.prepare_payment_transaction(
                        st.session_state.payment_submission,
                        max_gas_price_gwei=50
                    )
                except Exception as e:
                    st.error(f"Error preparing transaction: {e}")
                    return

            col1, col2 = st.columns([2, 1])

            with col1:
                st.success("✅ Transaction parameters prepared")
                st.json(tx_prepared['transaction'])

            with col2:
                tx_params = tx_prepared['transaction']
                gas_price_gwei = service.web3.from_wei(tx_params['gasPrice'], 'gwei')
                currency = service.token_symbol if hasattr(service, 'token_symbol') else "ETH"

                # For ERC20, show token amount; for ETH, show value
                if currency == "USDC" or hasattr(service, 'token_address'):
                    amount_display = f"{st.session_state.payment_amount} {currency}"
                else:
                    amount_display = f"{service.web3.from_wei(tx_params['value'], 'ether')} ETH"

                st.info(f"""
                **Transaction Details**

                To: `{tx_params['to'][:10]}...`

                Amount: **{amount_display}**

                Gas: **{tx_params['gas']}**

                Gas Price: **{float(gas_price_gwei):.2f} Gwei**
                """)

            if st.session_state.payment_step == 4:
                if st.button("➡️ Send Transaction", type="primary"):
                    st.session_state.payment_step = 5
                    st.rerun()

        st.markdown("---")

    # ========================================================================
    # STEP 5: Payer Sends Transaction On-Chain
    # ========================================================================
    if st.session_state.payment_step >= 5:
        with st.container():
            st.markdown("### 5️⃣ Payer Broadcasts Transaction On-Chain")

            if st.session_state.tx_hash is None:
                with st.spinner("Payer signing and broadcasting transaction..."):
                    try:
                        # Get transaction params
                        tx_prepared = service.prepare_payment_transaction(
                            st.session_state.payment_submission,
                            max_gas_price_gwei=50
                        )

                        # Payer signs and sends
                        payer_account = Account.from_key(PAYER_PRIVATE_KEY)
                        tx_params = tx_prepared['transaction']
                        signed_tx = service.web3.eth.account.sign_transaction(tx_params, payer_account.key)

                        # Broadcast
                        tx_hash = service.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                        tx_hash_hex = tx_hash.hex()

                        # Wait for confirmation
                        receipt = service.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

                        st.session_state.tx_hash = tx_hash_hex
                        st.session_state.receipt = receipt
                    except Exception as e:
                        st.error(f"Error sending transaction: {e}")
                        return

            col1, col2 = st.columns([2, 1])

            with col1:
                st.success("✅ Transaction mined on blockchain!")

                tx_info = {
                    "tx_hash": st.session_state.tx_hash,
                    "block_number": st.session_state.receipt['blockNumber'],
                    "gas_used": st.session_state.receipt['gasUsed'],
                    "status": "Success" if st.session_state.receipt['status'] == 1 else "Failed"
                }
                st.json(tx_info)

            with col2:
                st.info(f"""
                **Blockchain Confirmation**

                Block: **{st.session_state.receipt['blockNumber']}**

                Gas Used: **{st.session_state.receipt['gasUsed']}**

                Status: **Success ✓**
                """)

                # Show block explorer link (Arc testnet or other network)
                # Get chain ID from environment or use Anvil default
                chain_id = int(os.getenv('PAYMENT_CHAIN_ID', str(ANVIL_CHAIN_ID)))
                explorer_url = get_tx_url(st.session_state.tx_hash, chain_id)

                if explorer_url != "#":
                    st.markdown(f"[🔍 View on Explorer ↗]({explorer_url})")
                else:
                    st.caption("(Local Anvil - No block explorer)")

            if st.session_state.payment_step == 5:
                if st.button("➡️ Verify Payment", type="primary"):
                    st.session_state.payment_step = 6
                    st.rerun()

        st.markdown("---")

    # ========================================================================
    # STEP 6: Merchant Verifies Transaction Received
    # ========================================================================
    if st.session_state.payment_step >= 6:
        with st.container():
            st.markdown("### 6️⃣ Merchant Verifies Payment Received")

            if st.session_state.payment_result is None:
                with st.spinner("Merchant verifying transaction..."):
                    try:
                        payment_result = service.verify_transaction_received(
                            st.session_state.tx_hash,
                            st.session_state.payment_submission
                        )
                        st.session_state.payment_result = payment_result
                    except Exception as e:
                        st.error(f"Error verifying transaction: {e}")
                        return

            if st.session_state.payment_result.get('type') == 'payment-completed':
                st.success("✅ Payment verified and completed!")

                col1, col2 = st.columns([2, 1])

                with col1:
                    st.json(st.session_state.payment_result)

                with col2:
                    st.success(f"""
                    **Payment Complete**

                    ✓ Amount verified

                    ✓ Sender verified

                    ✓ Recipient verified

                    ✓ Transaction confirmed
                    """)

                # Show final balances
                st.markdown("### 💰 Final Balances")
                col1, col2, col3 = st.columns(3)

                currency = service.token_symbol if hasattr(service, 'token_symbol') else "ETH"
                decimals = 2 if currency == "USDC" else 4

                with col1:
                    try:
                        merchant_balance = service.get_balance()
                        st.metric("Merchant Balance", f"{float(merchant_balance):.{decimals}f} {currency}", f"+{st.session_state.payment_amount} {currency}")
                    except:
                        st.metric("Merchant Balance", "Error")

                with col2:
                    try:
                        if currency == "USDC" or hasattr(service, 'token_address'):
                            # For ERC20, need to call balanceOf - skip for now
                            st.metric("Payer Balance", f"- {currency}", f"-{st.session_state.payment_amount} {currency}")
                        else:
                            payer_balance = service.web3.eth.get_balance(PAYER_ADDRESS)
                            payer_balance_eth = service.web3.from_wei(payer_balance, 'ether')
                            st.metric("Payer Balance", f"{float(payer_balance_eth):.4f} ETH", f"-{st.session_state.payment_amount} ETH")
                    except:
                        st.metric("Payer Balance", "Error")

                with col3:
                    gas_cost = st.session_state.receipt['gasUsed'] * service.web3.eth.gas_price
                    gas_cost_eth = service.web3.from_wei(gas_cost, 'ether')
                    st.metric("Gas Cost", f"{float(gas_cost_eth):.6f} ETH")

                if st.session_state.payment_step == 6:
                    if st.button("✅ Complete Demo", type="primary"):
                        st.session_state.payment_step = 7
                        st.rerun()
            else:
                st.error("❌ Payment verification failed")
                st.json(st.session_state.payment_result)

        st.markdown("---")

    # ========================================================================
    # STEP 7: Summary
    # ========================================================================
    if st.session_state.payment_step >= 7:
        st.success("### 🎉 Payment Flow Complete!")

        st.markdown("""
        The x402 payment protocol flow has been successfully demonstrated:

        1. ✅ Merchant created payment request (HTTP 402)
        2. ✅ Payer signed payment intent off-chain
        3. ✅ Merchant verified cryptographic signature
        4. ✅ Merchant prepared transaction parameters
        5. ✅ Payer broadcasted transaction on-chain
        6. ✅ Merchant verified payment received
        7. ✅ Payment completed and balances updated

        **Key Features Demonstrated:**
        - Cryptographic signature verification
        - On-chain settlement
        - Balance verification
        - Secure payment flow
        - Agent-to-agent payments (A2A)
        """)

        if st.button("🔄 Start New Payment Demo", type="primary"):
            st.session_state.payment_step = 0
            st.session_state.payment_request = None
            st.session_state.payment_submission = None
            st.session_state.tx_hash = None
            st.session_state.payment_result = None
            st.rerun()
