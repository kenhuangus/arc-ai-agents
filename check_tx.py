#!/usr/bin/env python3
"""Check transaction status on Arc testnet"""

from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv('config/.env')

# Arc Testnet
RPC_URL = os.getenv('PAYMENT_RPC_URL', 'https://rpc.testnet.arc.network')
w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    print("❌ Failed to connect to Arc testnet")
    exit(1)

print(f"✅ Connected to Arc testnet (Chain ID: {w3.eth.chain_id})")

# Transaction hash from user's error
tx_hash = "0x8b936be3da83ec2dd01e4576d933622e31095acaae56b60da064ff086dbe553f"

print(f"\n🔍 Checking transaction: {tx_hash}")
print(f"Explorer: https://testnet.arcscan.app/tx/{tx_hash}")

try:
    # Try to get transaction
    tx = w3.eth.get_transaction(tx_hash)
    print("\n✅ Transaction found!")
    print(f"  From: {tx['from']}")
    print(f"  To: {tx['to']}")
    print(f"  Value: {tx['value']}")
    print(f"  Gas: {tx['gas']}")
    print(f"  Gas Price: {w3.from_wei(tx['gasPrice'], 'gwei')} Gwei")
    print(f"  Nonce: {tx['nonce']}")

    # Try to get receipt
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        print(f"\n✅ Transaction confirmed!")
        print(f"  Block: {receipt['blockNumber']}")
        print(f"  Gas Used: {receipt['gasUsed']}")
        print(f"  Status: {'Success ✓' if receipt['status'] == 1 else 'Failed ✗'}")
    except Exception as e:
        print(f"\n⏳ Transaction pending (not mined yet)")
        print(f"  The transaction exists but hasn't been included in a block yet")

except Exception as e:
    print(f"\n❌ Transaction not found: {e}")
    print("The transaction was never broadcast or doesn't exist on this network")
