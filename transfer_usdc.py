#!/usr/bin/env python3
"""
Transfer USDC from Merchant to Payer on Arc Testnet
"""

from web3 import Web3
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('config/.env')

# Arc Testnet Configuration
RPC_URL = os.getenv('PAYMENT_RPC_URL', 'https://rpc.testnet.arc.network')
USDC_ADDRESS = os.getenv('PAYMENT_TOKEN_ADDRESS', '0x3600000000000000000000000000000000000000')

# Accounts (from x402_payment_demo.py)
MERCHANT_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
MERCHANT_ADDRESS = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"

PAYER_ADDRESS = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"

# Connect to Arc testnet
w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    print("❌ Failed to connect to Arc testnet")
    exit(1)

print(f"✅ Connected to Arc testnet (Chain ID: {w3.eth.chain_id})")

# ERC-20 ABI (minimal - just what we need)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

# Get USDC contract
usdc = w3.eth.contract(address=Web3.to_checksum_address(USDC_ADDRESS), abi=ERC20_ABI)

# Check balances before
print("\n📊 Balances BEFORE transfer:")
merchant_balance_before = usdc.functions.balanceOf(MERCHANT_ADDRESS).call()
payer_balance_before = usdc.functions.balanceOf(PAYER_ADDRESS).call()

print(f"Merchant ({MERCHANT_ADDRESS[:10]}...): {merchant_balance_before / 1e6:.6f} USDC")
print(f"Payer ({PAYER_ADDRESS[:10]}...): {payer_balance_before / 1e6:.6f} USDC")

# Transfer amount: 5 USDC (5,000,000 wei with 6 decimals)
transfer_amount = 5_000_000
print(f"\n💸 Transferring {transfer_amount / 1e6:.2f} USDC from Merchant to Payer...")

# Create merchant account from private key
merchant_account = w3.eth.account.from_key(MERCHANT_PRIVATE_KEY)

# Build transfer transaction
transfer_txn = usdc.functions.transfer(
    PAYER_ADDRESS,
    transfer_amount
).build_transaction({
    'from': MERCHANT_ADDRESS,
    'nonce': w3.eth.get_transaction_count(MERCHANT_ADDRESS),
    'gas': 100000,
    'gasPrice': w3.eth.gas_price,
})

# Sign transaction
signed_txn = merchant_account.sign_transaction(transfer_txn)

# Send transaction
print("📤 Sending transaction...")
tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
print(f"Transaction Hash: {tx_hash.hex()}")
print(f"Explorer: https://testnet.arcscan.app/tx/{tx_hash.hex()}")

# Wait for confirmation
print("⏳ Waiting for confirmation...")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

if receipt['status'] == 1:
    print("✅ Transfer successful!")
else:
    print("❌ Transfer failed!")
    exit(1)

# Check balances after
print("\n📊 Balances AFTER transfer:")
merchant_balance_after = usdc.functions.balanceOf(MERCHANT_ADDRESS).call()
payer_balance_after = usdc.functions.balanceOf(PAYER_ADDRESS).call()

print(f"Merchant ({MERCHANT_ADDRESS[:10]}...): {merchant_balance_after / 1e6:.6f} USDC")
print(f"Payer ({PAYER_ADDRESS[:10]}...): {payer_balance_after / 1e6:.6f} USDC")

# Verify transfer
expected_merchant = merchant_balance_before - transfer_amount
expected_payer = payer_balance_before + transfer_amount

if merchant_balance_after == expected_merchant and payer_balance_after == expected_payer:
    print("\n✅ Transfer verified! Payer now has sufficient USDC for x402 demo.")
else:
    print("\n⚠️ Balance mismatch detected!")
    print(f"Expected Merchant: {expected_merchant / 1e6:.6f}, Got: {merchant_balance_after / 1e6:.6f}")
    print(f"Expected Payer: {expected_payer / 1e6:.6f}, Got: {payer_balance_after / 1e6:.6f}")
