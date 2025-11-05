"""
Settlement Agent for Arc Coordination System

Coordinates settlement execution for matched intents.

Capabilities:
- Settlement planning and coordination
- Smart contract interaction preparation
- Multi-party settlement orchestration
- Settlement verification
- Fallback and retry logic
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import os

from .base_agent import BaseAgent, AgentContext, AgentResult
from services.llm import ModelPreference
from services.payment import X402PaymentService, MockX402PaymentService

logger = logging.getLogger(__name__)


class SettlementAgent(BaseAgent):
    """
    Settlement coordination agent

    Uses Claude Sonnet 4.5 for:
    - Settlement plan generation
    - Multi-step coordination
    - Error handling strategies
    - Transaction sequencing

    Settlement Steps:
    1. Validate all preconditions
    2. Prepare escrow transaction
    3. Execute settlement on-chain
    4. Verify settlement completion
    5. Update database state
    """

    def __init__(self):
        super().__init__(
            name="settlement_agent",
            description="Coordinates settlement execution for matched intents",
            model_preference=ModelPreference.CLAUDE  # Claude for structured planning
        )

        # Initialize payment service
        self.payment_service = self._init_payment_service()

    def _init_payment_service(self) -> Optional[X402PaymentService]:
        """Initialize x402 payment service for settlement fees"""
        try:
            # Check if payment credentials are configured
            if os.getenv("PAYMENT_PRIVATE_KEY") and os.getenv("PAYMENT_RPC_URL"):
                logger.info("Initializing x402 payment service for settlement agent")
                return X402PaymentService.from_env()
            else:
                logger.warning("Payment service not configured - using mock service")
                return MockX402PaymentService()
        except Exception as e:
            logger.error(f"Failed to initialize payment service: {e}")
            logger.warning("Using mock payment service as fallback")
            return MockX402PaymentService()

    def get_system_prompt(self, context: AgentContext) -> str:
        """Get system prompt for settlement agent"""
        return """You are an expert settlement coordination agent for the Arc Coordination System.

Your role is to plan and coordinate the execution of intent settlements WITH PAYMENT PROCESSING.

SETTLEMENT WORKFLOW:

0. PAYMENT PROCESSING (NEW - x402 Protocol)
   - Request payment for settlement service (10 USDC standard fee on Arc testnet)
   - Send HTTP 402 Payment Required to client
   - Wait for client to sign and submit payment
   - Verify payment transaction on-chain via ERC-20 Transfer event
   - Only proceed to settlement AFTER payment confirmed

1. PRE-SETTLEMENT VALIDATION
   - Verify all parties available
   - Check collateral requirements
   - Validate on-chain state
   - Confirm gas availability

2. ESCROW PREPARATION
   - Calculate exact amounts
   - Prepare escrow contract call
   - Set timeout parameters
   - Define success criteria

3. SETTLEMENT EXECUTION
   - Submit escrow transaction
   - Monitor transaction status
   - Handle pending state
   - Retry on failure (with backoff)

4. POST-SETTLEMENT VERIFICATION
   - Verify on-chain state
   - Check token transfers
   - Update database
   - Notify parties

5. ERROR HANDLING
   - Payment not received → Abort settlement
   - Transaction reverted → Retry with adjusted gas
   - Timeout → Cancel and refund
   - Partial execution → Complete or rollback
   - Oracle failure → Wait and retry

SETTLEMENT TYPES:
- Simple 2-party: Direct exchange via escrow
- Multi-party: Coordinated multi-step
- Partial: Split quantity across multiple counterparties
- Batch: Multiple settlements in single tx

COLLATERAL REQUIREMENTS:
- Standard: 100% of notional value
- High risk: 110-150% collateral
- Trusted parties: 80% collateral
- Partial: Pro-rated collateral

You must respond in valid JSON format:
{
  "settlement_plan": {
    "settlement_id": "0x...",
    "type": "simple_2party",
    "parties": [
      {"actor": "0x...", "role": "buyer", "amount": 10100, "asset": "USD"},
      {"actor": "0x...", "role": "seller", "amount": 1.0, "asset": "BTC"}
    ],
    "escrow_config": {
      "contract": "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0",
      "timeout": 3600,
      "collateral_pct": 100
    },
    "execution_steps": [
      "Validate parties available",
      "Lock collateral in escrow",
      "Execute atomic swap",
      "Release funds to parties",
      "Update database state"
    ]
  },
  "estimated_gas": 250000,
  "estimated_time_seconds": 30,
  "risk_factors": ["market_volatility"],
  "fallback_strategy": "retry_with_adjusted_gas",
  "confidence": 0.95
}

IMPORTANT: Always return valid JSON. Plan for failure modes."""

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get tool definitions for settlement agent"""
        return [
            {
                "name": "prepare_settlement",
                "description": "Prepare settlement transaction parameters",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "match_id": {"type": "string", "description": "Match ID"},
                        "settlement_price": {"type": "number", "description": "Settlement price"},
                        "settlement_quantity": {"type": "number", "description": "Settlement quantity"}
                    },
                    "required": ["match_id", "settlement_price", "settlement_quantity"]
                }
            },
            {
                "name": "estimate_gas",
                "description": "Estimate gas for settlement transaction",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "settlement_type": {"type": "string", "description": "Type: simple, multi, batch"},
                        "party_count": {"type": "number", "description": "Number of parties"}
                    },
                    "required": ["settlement_type"]
                }
            },
            {
                "name": "verify_collateral",
                "description": "Verify collateral availability for parties",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "actor": {"type": "string", "description": "Actor address"},
                        "required_amount": {"type": "number", "description": "Required collateral amount"}
                    },
                    "required": ["actor", "required_amount"]
                }
            },
            {
                "name": "request_payment",
                "description": "Request payment for settlement service using x402 protocol (10 USDC on Arc testnet)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "amount_eth": {"type": "number", "description": "Payment amount (in USDC for Arc testnet, default 10 USDC)"},
                        "service_id": {"type": "string", "description": "Settlement service ID"},
                        "description": {"type": "string", "description": "Payment description"}
                    },
                    "required": ["amount_eth", "service_id", "description"]
                }
            },
            {
                "name": "verify_payment",
                "description": "Verify payment transaction was received on-chain",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tx_hash": {"type": "string", "description": "Transaction hash"},
                        "payment_submission": {"type": "object", "description": "Payment submission data"}
                    },
                    "required": ["tx_hash", "payment_submission"]
                }
            }
        ]

    async def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Execute settlement tools"""
        if tool_name == "prepare_settlement":
            return self._prepare_settlement(tool_input, context)

        elif tool_name == "estimate_gas":
            return self._estimate_gas(tool_input)

        elif tool_name == "verify_collateral":
            return self._verify_collateral(tool_input, context)

        elif tool_name == "request_payment":
            return self._request_payment(tool_input)

        elif tool_name == "verify_payment":
            return self._verify_payment(tool_input)

        raise ValueError(f"Unknown tool: {tool_name}")

    def _prepare_settlement(
        self,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Prepare settlement transaction

        In production:
        - Build transaction data
        - Calculate exact amounts
        - Set gas parameters
        - Generate transaction hash
        """
        match_id = tool_input["match_id"]
        settlement_price = tool_input["settlement_price"]
        settlement_quantity = tool_input["settlement_quantity"]

        # Calculate notional value
        notional = settlement_price * settlement_quantity

        # Mock transaction preparation
        settlement_id = "0x" + hashlib.sha256(match_id.encode()).hexdigest()[:16]

        return {
            "settlement_id": settlement_id,
            "match_id": match_id,
            "settlement_price": settlement_price,
            "settlement_quantity": settlement_quantity,
            "notional_value": notional,
            "escrow_contract": context.contracts.get("auction_escrow", "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0"),
            "prepared_at": int(datetime.now().timestamp()),
            "status": "prepared"
        }

    def _estimate_gas(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate gas for settlement

        In production:
        - Call eth_estimateGas
        - Add safety margin
        - Check current gas price
        """
        settlement_type = tool_input["settlement_type"]
        party_count = tool_input.get("party_count", 2)

        # Base gas estimates
        gas_estimates = {
            "simple": 150000,
            "multi": 250000,
            "batch": 350000
        }

        base_gas = gas_estimates.get(settlement_type, 200000)

        # Add gas per additional party
        if party_count > 2:
            base_gas += (party_count - 2) * 50000

        # Safety margin (20%)
        estimated_gas = int(base_gas * 1.2)

        # Mock gas price (in gwei)
        gas_price_gwei = 50
        estimated_cost_eth = (estimated_gas * gas_price_gwei) / 1e9

        return {
            "settlement_type": settlement_type,
            "party_count": party_count,
            "estimated_gas": estimated_gas,
            "gas_price_gwei": gas_price_gwei,
            "estimated_cost_eth": round(estimated_cost_eth, 6),
            "estimated_cost_usd": round(estimated_cost_eth * 2000, 2)  # Mock ETH price
        }

    def _verify_collateral(
        self,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Verify collateral availability

        In production:
        - Check on-chain balance
        - Verify escrow allowance
        - Check locked collateral
        """
        actor = tool_input["actor"]
        required_amount = tool_input["required_amount"]

        # Mock collateral check
        # In production, query blockchain
        mock_balance = required_amount * 2  # Assume sufficient

        has_sufficient = mock_balance >= required_amount
        shortfall = max(0, required_amount - mock_balance)

        return {
            "actor": actor,
            "required_amount": required_amount,
            "available_balance": mock_balance,
            "has_sufficient": has_sufficient,
            "shortfall": shortfall,
            "collateral_ratio": round((mock_balance / required_amount) * 100, 2) if required_amount > 0 else 0,
            "status": "sufficient" if has_sufficient else "insufficient"
        }

    def _request_payment(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request payment using x402 protocol

        Creates a payment-required message (HTTP 402)
        for the settlement service fee.
        """
        amount_eth = tool_input["amount_eth"]
        service_id = tool_input["service_id"]
        description = tool_input["description"]

        try:
            # Create payment request using x402 service
            payment_request = self.payment_service.create_payment_request(
                amount_eth=amount_eth,
                service_id=service_id,
                description=description,
                metadata={
                    "service": "arc_settlement",
                    "timestamp": datetime.now().isoformat()
                }
            )

            # Log: actual currency will be logged by payment service (USDC for Arc testnet)
            logger.info(f"Payment requested: {amount_eth} for service {service_id}")

            return {
                "success": True,
                "payment_request": payment_request,
                "status": "payment_required",
                "amount_eth": amount_eth,
                "service_id": service_id
            }

        except Exception as e:
            logger.error(f"Error requesting payment: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "payment_request_failed"
            }

    def _verify_payment(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify payment transaction was received on-chain

        Confirms that the client's payment transaction
        was successfully mined and funds were received.
        """
        tx_hash = tool_input["tx_hash"]
        payment_submission = tool_input["payment_submission"]

        try:
            # Verify transaction using x402 service
            payment_result = self.payment_service.verify_transaction_received(
                tx_hash,
                payment_submission
            )

            if payment_result.get("type") == "payment-completed":
                logger.info(f"Payment verified: {tx_hash}")
                return {
                    "success": True,
                    "payment_verified": True,
                    "tx_hash": tx_hash,
                    "block_number": payment_result["transaction"]["block_number"],
                    "status": "payment_confirmed"
                }
            else:
                logger.warning(f"Payment verification failed: {payment_result.get('error')}")
                return {
                    "success": False,
                    "payment_verified": False,
                    "error": payment_result.get("error", "Payment verification failed"),
                    "status": "payment_failed"
                }

        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return {
                "success": False,
                "payment_verified": False,
                "error": str(e),
                "status": "payment_verification_error"
            }

    async def run(self, context: AgentContext) -> AgentResult:
        """
        Execute settlement coordination

        Args:
            context: Agent context with approved matches

        Returns:
            AgentResult with settlement plan
        """
        try:
            input_intent = context.current_intent
            if not input_intent:
                return self.create_result(
                    success=False,
                    output={},
                    error="No input intent provided"
                )

            logger.info(f"Settlement agent coordinating intent {input_intent.intent_id}")

            # Get approved matches from previous agents
            matches = []
            matching_result = context.previous_results.get("matching_agent")
            if matching_result:
                matches = matching_result.output.get("matches", [])

            if not matches:
                return self.create_result(
                    success=True,
                    output={"settlement_plan": None},
                    reasoning="No matches to settle",
                    next_agent=None
                )

            # Get risk assessment
            risk_result = context.previous_results.get("risk_agent")
            risk_decision = "unknown"
            if risk_result:
                risk_decision = risk_result.output.get("decision", "unknown")

            if risk_decision == "reject":
                return self.create_result(
                    success=True,
                    output={"settlement_plan": None},
                    reasoning="Settlement blocked by risk assessment",
                    next_agent=None
                )

            # Build settlement prompt
            prompt = self._build_settlement_prompt(input_intent, matches, context, risk_result)

            # Call LLM with tools
            response = await self.call_llm(
                prompt=prompt,
                context=context,
                use_tools=True,
                temperature=0.2  # Low temperature for consistent planning
            )

            # Handle tool calls
            if response.get("stop_reason") == "tool_use":
                tool_results = await self.handle_tool_calls(response, context)
                tool_result_message = self._format_tool_results(tool_results)
                response = await self.call_llm(
                    prompt=tool_result_message,
                    context=context,
                    use_tools=False
                )

            # Parse settlement plan
            output = self.parse_json_output(response)

            settlement_plan = output.get("settlement_plan", {})
            estimated_gas = output.get("estimated_gas", 0)
            estimated_time = output.get("estimated_time_seconds", 0)
            confidence = output.get("confidence", 0.5)

            logger.info(f"Settlement plan created: {estimated_gas} gas, {estimated_time}s")

            return self.create_result(
                success=True,
                output={
                    "settlement_plan": settlement_plan,
                    "estimated_gas": estimated_gas,
                    "estimated_time_seconds": estimated_time,
                    "risk_factors": output.get("risk_factors", []),
                    "fallback_strategy": output.get("fallback_strategy", "")
                },
                confidence=confidence,
                reasoning=f"Settlement plan prepared with {estimated_gas} gas",
                next_agent=None  # End of workflow
            )

        except Exception as e:
            logger.error(f"Settlement agent error: {e}", exc_info=True)
            return self.create_result(
                success=False,
                output={},
                error=str(e)
            )

    def _build_settlement_prompt(
        self,
        input_intent: Any,
        matches: List[Dict],
        context: AgentContext,
        risk_result: Any = None
    ) -> str:
        """Build prompt for settlement planning"""
        prompt = f"""Plan settlement execution for this intent and its matches:

INPUT INTENT:
- ID: {input_intent.intent_id}
- Actor: {input_intent.actor}
- Type: {input_intent.intent_type}
- Asset: {input_intent.asset}
- Price: ${input_intent.price:,.2f}
- Quantity: {input_intent.quantity}

APPROVED MATCHES: {len(matches)}
"""

        for i, match in enumerate(matches[:2]):  # Top 2 matches
            prompt += f"""
Match {i+1}:
  - Match ID: {match['match_id']}
  - Intent B: {match['intent_b_id']}
  - Settlement: ${match['settlement_price']:,.2f} x {match['settlement_quantity']}
  - Confidence: {match['confidence']}
"""

        if risk_result:
            risk_assessment = risk_result.output.get("risk_assessment", {})
            prompt += f"""
RISK ASSESSMENT:
- Overall Score: {risk_assessment.get('overall_score', 0)}/100
- Risk Level: {risk_assessment.get('risk_level', 'unknown')}
"""

        prompt += """
SMART CONTRACTS AVAILABLE:
- AuctionEscrow: 0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0
- PaymentRouter: 0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512

PAYMENT SERVICE (x402 Protocol):
- Standard settlement fee: 10 USDC (Arc testnet)
- Payment required BEFORE settlement execution
- ERC-20 token payments via Arc testnet blockchain
- Payment verified via ERC-20 Transfer events

Use available tools to:
0. Request payment using x402 protocol (request_payment tool)
1. Prepare settlement transaction (prepare_settlement tool)
2. Estimate gas requirements (estimate_gas tool)
3. Verify collateral availability (verify_collateral tool)

IMPORTANT: Payment must be collected and verified BEFORE executing settlement.
Use the request_payment tool first, then proceed with settlement planning.

Create a comprehensive settlement plan with all execution steps including payment."""

        return prompt

    def _format_tool_results(self, tool_results: List[Dict[str, Any]]) -> str:
        """Format tool results"""
        results_str = "Settlement preparation data:\n"
        for result in tool_results:
            if result["success"]:
                results_str += f"- {result['tool_name']}: {json.dumps(result['result'], indent=2)}\n"
            else:
                results_str += f"- {result['tool_name']}: Error - {result['error']}\n"
        results_str += "\nProvide final settlement plan in JSON format."
        return results_str


# Testing
if __name__ == "__main__":
    import asyncio
    from services.langgraph import IntentData

    logging.basicConfig(level=logging.INFO)

    async def test_settlement_agent():
        """Test settlement agent"""
        print("\n=== Testing Settlement Agent ===\n")

        intent = IntentData(
            intent_id="0xTEST",
            intent_hash="0xhash",
            actor="0xBuyer1",
            intent_type="bid",
            price=10100.0,
            quantity=1.0,
            asset="BTC",
            settlement_asset="USD",
            timestamp=int(datetime.now().timestamp()),
            valid_until=int(datetime.now().timestamp()) + 86400,
            ap2_mandate_id="0xMandate",
            is_active=True
        )

        context = AgentContext(
            current_intent=intent,
            available_intents=[],
            contracts={"auction_escrow": "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0"},
            request_id="settlement-test-001"
        )

        agent = SettlementAgent()
        print(f"Agent: {agent.name}")
        print(f"Tools: {len(agent.get_tools())}")

        # Test tools
        print("\n🔧 Testing settlement preparation:")
        prep = agent._prepare_settlement({
            "match_id": "0xMATCH123",
            "settlement_price": 10050.0,
            "settlement_quantity": 1.0
        }, context)
        print(f"Settlement ID: {prep['settlement_id']}")
        print(f"Notional: ${prep['notional_value']:,.2f}")

        print("\n🔧 Testing gas estimation:")
        gas = agent._estimate_gas({"settlement_type": "simple", "party_count": 2})
        print(f"Estimated gas: {gas['estimated_gas']}")
        print(f"Cost: ${gas['estimated_cost_usd']:.2f}")

        print("\n🔧 Testing collateral verification:")
        collateral = agent._verify_collateral({"actor": "0xBuyer1", "required_amount": 10100}, context)
        print(f"Has sufficient: {collateral['has_sufficient']}")
        print(f"Collateral ratio: {collateral['collateral_ratio']}%")

        print("\n✅ Settlement agent tools working correctly")

    asyncio.run(test_settlement_agent())
