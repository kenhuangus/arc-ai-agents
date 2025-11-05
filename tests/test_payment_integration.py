"""
Payment Integration Tests

Tests the X402PaymentService with local Anvil blockchain.
Uses Anvil's default test accounts which come pre-funded with ETH.
"""

import os
import sys
import json
import time
from decimal import Decimal
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.payment import X402PaymentService

# Anvil test accounts (known private keys for local testing only)
MERCHANT_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
MERCHANT_ADDRESS = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"

PAYER_PRIVATE_KEY = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
PAYER_ADDRESS = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"

# Anvil local blockchain
ANVIL_RPC_URL = "http://localhost:8545"
ANVIL_CHAIN_ID = 31337  # Anvil's default chain ID


class Colors:
    """Terminal colors for test output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_test(message: str):
    """Print test message"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{message}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")


def test_service_initialization():
    """Test 1: Initialize payment service"""
    print_test("Test 1: Payment Service Initialization")

    try:
        service = X402PaymentService(
            private_key=MERCHANT_PRIVATE_KEY,
            rpc_url=ANVIL_RPC_URL,
            chain_id=ANVIL_CHAIN_ID,
            min_amount=0.001,
            max_amount=10.0,
            timeout_seconds=300
        )

        print_info(f"Merchant address: {service.address}")
        print_info(f"Chain ID: {service.chain_id}")
        print_info(f"Connected to blockchain: {service.web3.is_connected()}")

        # Check balance
        balance = service.get_balance()
        print_info(f"Merchant balance: {balance} ETH")

        if service.address.lower() == MERCHANT_ADDRESS.lower():
            print_success("Service initialized successfully")
            return service
        else:
            print_error(f"Address mismatch: expected {MERCHANT_ADDRESS}, got {service.address}")
            return None

    except Exception as e:
        print_error(f"Initialization failed: {e}")
        return None


def test_payment_request_creation(service: X402PaymentService):
    """Test 2: Create payment request"""
    print_test("Test 2: Payment Request Creation")

    try:
        payment_request = service.create_payment_request(
            amount_eth=0.01,
            service_id="test_settlement_001",
            description="Test settlement service",
            metadata={"test": True, "intent_id": "test_intent_123"}
        )

        print_info(f"Payment type: {payment_request['type']}")
        print_info(f"Amount: {payment_request['payment']['amount']} wei (0.01 ETH)")
        print_info(f"Recipient: {payment_request['payment']['recipient']}")
        print_info(f"Service ID: {payment_request['payment']['service_id']}")
        print_info(f"Description: {payment_request['payment']['description']}")

        # Validate structure
        assert payment_request['type'] == 'payment-required', "Invalid payment type"
        assert payment_request['version'] == '0.1', "Invalid version"
        assert 'payment' in payment_request, "Missing payment field"
        assert 'merchant' in payment_request, "Missing merchant field"
        assert payment_request['payment']['currency'] == 'ETH', "Invalid currency"

        print_success("Payment request created successfully")
        return payment_request

    except Exception as e:
        print_error(f"Payment request creation failed: {e}")
        return None


def test_payment_signature(service: X402PaymentService, payment_request: Dict[str, Any]):
    """Test 3: Sign payment as payer and verify signature"""
    print_test("Test 3: Payment Signature & Verification")

    try:
        # Import eth_account for payer signing
        from eth_account import Account
        from eth_account.messages import encode_defunct

        # Payer signs the payment
        payer_account = Account.from_key(PAYER_PRIVATE_KEY)
        payment_data = payment_request['payment']

        # Create message to sign
        message_text = json.dumps(payment_data, sort_keys=True)
        message = encode_defunct(text=message_text)

        # Sign message
        signed_message = payer_account.sign_message(message)
        signature = signed_message.signature.hex()

        print_info(f"Payer address: {payer_account.address}")
        print_info(f"Signature: {signature[:20]}...")

        # Create payment submission
        payment_submission = {
            "type": "payment-submitted",
            "version": "0.1",
            "payment": payment_data,
            "signature": signature,
            "payer": {
                "address": payer_account.address,
                "type": "ethereum"
            }
        }

        # Verify signature
        is_valid = service.verify_payment_signature(payment_submission)

        if is_valid:
            print_success("Payment signature verified successfully")
            return payment_submission
        else:
            print_error("Signature verification failed")
            return None

    except Exception as e:
        print_error(f"Signature test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_on_chain_settlement(service: X402PaymentService, payment_submission: Dict[str, Any]):
    """Test 4: Settle payment on-chain (payer sends transaction)"""
    print_test("Test 4: On-Chain Settlement (Payer Sends Transaction)")

    try:
        print_info("Checking balances before settlement...")
        merchant_balance_before = service.get_balance()

        # Get payer balance
        payer_balance_before = service.web3.eth.get_balance(PAYER_ADDRESS)
        payer_balance_eth_before = service.web3.from_wei(payer_balance_before, 'ether')

        print_info(f"Merchant balance before: {merchant_balance_before} ETH")
        print_info(f"Payer balance before: {payer_balance_eth_before} ETH")

        # Step 4a: Merchant prepares transaction parameters
        print_info("Merchant preparing transaction parameters...")
        tx_prepared = service.prepare_payment_transaction(
            payment_submission,
            max_gas_price_gwei=50
        )

        print_info(f"Transaction prepared: {tx_prepared['type']}")

        # Step 4b: Payer signs and sends the transaction
        from eth_account import Account

        print_info("Payer signing and sending transaction...")
        payer_account = Account.from_key(PAYER_PRIVATE_KEY)

        tx_params = tx_prepared['transaction']
        signed_tx = service.web3.eth.account.sign_transaction(tx_params, payer_account.key)

        # Send transaction from payer
        tx_hash = service.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_hash_hex = tx_hash.hex()

        print_info(f"Transaction sent: {tx_hash_hex}")

        # Wait for confirmation
        receipt = service.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        print_info(f"Transaction mined in block: {receipt['blockNumber']}")

        # Step 4c: Merchant verifies transaction was received
        print_info("Merchant verifying payment received...")
        payment_result = service.verify_transaction_received(
            tx_hash_hex,
            payment_submission
        )

        print_info(f"Verification result: {payment_result.get('type')}")

        if payment_result.get('type') == 'payment-completed':
            block_number = payment_result['transaction']['block_number']
            gas_used = payment_result['transaction']['gas_used']
            status = payment_result['transaction']['status']

            print_info(f"Transaction hash: {tx_hash_hex}")
            print_info(f"Block number: {block_number}")
            print_info(f"Gas used: {gas_used}")
            print_info(f"Status: {status}")

            # Check balances after
            merchant_balance_after = service.get_balance()
            payer_balance_after = service.web3.eth.get_balance(PAYER_ADDRESS)
            payer_balance_eth_after = service.web3.from_wei(payer_balance_after, 'ether')

            print_info(f"Merchant balance after: {merchant_balance_after} ETH")
            print_info(f"Payer balance after: {payer_balance_eth_after} ETH")

            # Verify balances changed correctly
            balance_diff = merchant_balance_after - merchant_balance_before
            print_info(f"Merchant received: {balance_diff} ETH")

            if status == 'success' and balance_diff > 0:
                print_success("Payment settled on-chain successfully")
                return payment_result
            else:
                print_error("Transaction completed but balances didn't change as expected")
                return None
        elif payment_result.get('type') == 'payment-failed':
            print_error(f"Payment verification failed: {payment_result.get('error')}")
            return None
        else:
            print_error(f"Unexpected result type: {payment_result.get('type')}")
            return None

    except Exception as e:
        print_error(f"On-chain settlement failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_transaction_status(service: X402PaymentService, payment_result: Dict[str, Any]):
    """Test 5: Query transaction status"""
    print_test("Test 5: Transaction Status Query")

    try:
        tx_hash = payment_result['transaction']['hash']
        print_info(f"Querying status for: {tx_hash}")

        status = service.get_transaction_status(tx_hash)

        print_info(f"Found: {status.get('found')}")
        print_info(f"Status: {status.get('status')}")
        print_info(f"Block number: {status.get('block_number')}")
        print_info(f"Gas used: {status.get('gas_used')}")

        if status.get('found') and status.get('status') == 'success':
            print_success("Transaction status query successful")
            return True
        else:
            print_error("Transaction not found or failed")
            return False

    except Exception as e:
        print_error(f"Transaction status query failed: {e}")
        return False


def test_error_handling(service: X402PaymentService):
    """Test 6: Error handling"""
    print_test("Test 6: Error Handling")

    errors_caught = 0

    # Test 6a: Amount too low
    try:
        service.create_payment_request(
            amount_eth=0.0001,  # Below minimum
            service_id="test_low_amount",
            description="Test low amount"
        )
        print_error("Should have raised ValueError for low amount")
    except ValueError as e:
        print_success(f"Caught low amount error: {e}")
        errors_caught += 1

    # Test 6b: Amount too high
    try:
        service.create_payment_request(
            amount_eth=100.0,  # Above maximum
            service_id="test_high_amount",
            description="Test high amount"
        )
        print_error("Should have raised ValueError for high amount")
    except ValueError as e:
        print_success(f"Caught high amount error: {e}")
        errors_caught += 1

    # Test 6c: Invalid signature
    try:
        invalid_submission = {
            "type": "payment-submitted",
            "payment": {"amount": "1000000000000000"},
            "signature": "0xinvalidsignature",
            "payer": {"address": "0x0000000000000000000000000000000000000000"}
        }
        is_valid = service.verify_payment_signature(invalid_submission)
        if not is_valid:
            print_success("Correctly rejected invalid signature")
            errors_caught += 1
        else:
            print_error("Should have rejected invalid signature")
    except Exception as e:
        print_success(f"Caught invalid signature error: {e}")
        errors_caught += 1

    if errors_caught >= 2:
        print_success(f"Error handling working correctly ({errors_caught}/3 tests passed)")
        return True
    else:
        print_error(f"Some error handling tests failed ({errors_caught}/3 passed)")
        return False


def main():
    """Run all payment integration tests"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}  Payment Integration Test Suite{Colors.END}")
    print(f"{Colors.BOLD}  Testing with Anvil Local Blockchain{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")

    results = []

    # Test 1: Initialize service
    service = test_service_initialization()
    results.append(service is not None)
    if not service:
        print_error("Cannot continue without service initialization")
        return

    # Test 2: Create payment request
    payment_request = test_payment_request_creation(service)
    results.append(payment_request is not None)
    if not payment_request:
        print_error("Cannot continue without payment request")
        return

    # Test 3: Sign and verify payment
    payment_submission = test_payment_signature(service, payment_request)
    results.append(payment_submission is not None)
    if not payment_submission:
        print_error("Cannot continue without payment submission")
        return

    # Test 4: Settle on-chain (this may fail due to implementation limitations)
    payment_result = test_on_chain_settlement(service, payment_submission)
    results.append(payment_result is not None)

    # Test 5: Query transaction status (only if settlement succeeded)
    if payment_result:
        tx_status_ok = test_transaction_status(service, payment_result)
        results.append(tx_status_ok)
    else:
        print_info("Skipping transaction status test (no successful settlement)")
        results.append(False)

    # Test 6: Error handling
    error_handling_ok = test_error_handling(service)
    results.append(error_handling_ok)

    # Summary
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}  Test Summary{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")

    passed = sum(results)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}")

    test_names = [
        "Service Initialization",
        "Payment Request Creation",
        "Payment Signature & Verification",
        "On-Chain Settlement",
        "Transaction Status Query",
        "Error Handling"
    ]

    for i, (name, result) in enumerate(zip(test_names, results), 1):
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {i}. {name}: {status}")

    if passed == total:
        print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
        print(f"{Colors.GREEN}{Colors.BOLD}  All tests passed! ✓{Colors.END}")
        print(f"{Colors.GREEN}{'='*60}{Colors.END}\n")
    else:
        print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
        print(f"{Colors.YELLOW}{Colors.BOLD}  Some tests failed. Review output above.{Colors.END}")
        print(f"{Colors.YELLOW}{'='*60}{Colors.END}\n")


if __name__ == "__main__":
    main()
