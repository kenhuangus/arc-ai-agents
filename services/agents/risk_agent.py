"""
Risk Agent for Arc Coordination System

Assesses risks associated with intent matches and settlements.

Capabilities:
- Evaluate counterparty risk
- Check position limits and exposure
- Assess market risk
- Calculate collateral requirements
- Determine acceptable risk levels for settlement
"""

import logging
import json
from typing import List, Dict, Any
from datetime import datetime
import hashlib

from .base_agent import BaseAgent, AgentContext, AgentResult
from services.llm import ModelPreference

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent):
    """
    Risk assessment agent

    Uses Claude Sonnet 4.5 for:
    - Structured risk scoring
    - Multi-factor risk analysis
    - Decision-making on proceed/reject
    - Risk mitigation recommendations

    Risk Categories:
    1. Counterparty Risk: Actor reputation and history
    2. Market Risk: Price volatility and exposure
    3. Settlement Risk: Settlement feasibility
    4. Operational Risk: System and execution risks
    5. Liquidity Risk: Ability to unwind positions
    """

    def __init__(self):
        super().__init__(
            name="risk_agent",
            description="Assesses risks for intent matches and settlements",
            model_preference=ModelPreference.CLAUDE  # Claude for structured decisions
        )

    def get_system_prompt(self, context: AgentContext) -> str:
        """Get system prompt for risk agent"""
        return """You are an expert risk assessment agent for the Arc Coordination System.

Your role is to evaluate risks associated with intent matches and make go/no-go decisions.

RISK ASSESSMENT FRAMEWORK:

1. COUNTERPARTY RISK (Weight: 30%)
   - Actor reputation score (0-100)
   - Historical success rate
   - Default history
   - Collateral posted

2. MARKET RISK (Weight: 25%)
   - Price volatility
   - Position size vs market depth
   - Concentration risk
   - Correlation risk

3. SETTLEMENT RISK (Weight: 25%)
   - Settlement complexity
   - Multi-party coordination
   - On-chain transaction risk
   - Time to settlement

4. OPERATIONAL RISK (Weight: 10%)
   - System availability
   - Smart contract risk
   - Oracle reliability

5. LIQUIDITY RISK (Weight: 10%)
   - Ability to unwind
   - Market impact
   - Liquidity reserves

RISK SCORING:
- 0-20: Critical risk - REJECT
- 21-40: High risk - Require additional collateral
- 41-60: Medium risk - Proceed with caution
- 61-80: Low risk - Proceed normally
- 81-100: Minimal risk - Fast-track

DECISION MATRIX:
- If any category scores <20: REJECT
- If overall score <40: Require mitigation
- If overall score 40-60: Proceed with monitoring
- If overall score >60: Approve

You must respond in valid JSON format:
{
  "risk_assessment": {
    "overall_score": 75,
    "risk_level": "low",
    "counterparty_risk": 80,
    "market_risk": 70,
    "settlement_risk": 75,
    "operational_risk": 85,
    "liquidity_risk": 70
  },
  "decision": "approve",
  "conditions": [
    "Monitor settlement execution",
    "Require 110% collateral"
  ],
  "reasoning": "Low overall risk with strong counterparty scores...",
  "confidence": 0.85
}

IMPORTANT: Always return valid JSON. No markdown, no code blocks."""

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get tool definitions for risk agent"""
        return [
            {
                "name": "check_actor_reputation",
                "description": "Check reputation and history of an actor",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "actor_address": {"type": "string", "description": "Actor's address"}
                    },
                    "required": ["actor_address"]
                }
            },
            {
                "name": "calculate_exposure",
                "description": "Calculate risk exposure for a position",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "price": {"type": "number", "description": "Settlement price"},
                        "quantity": {"type": "number", "description": "Settlement quantity"},
                        "asset": {"type": "string", "description": "Asset symbol"}
                    },
                    "required": ["price", "quantity", "asset"]
                }
            },
            {
                "name": "check_position_limits",
                "description": "Check if position exceeds risk limits",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "actor_address": {"type": "string", "description": "Actor's address"},
                        "asset": {"type": "string", "description": "Asset symbol"},
                        "quantity": {"type": "number", "description": "Position size"}
                    },
                    "required": ["actor_address", "asset", "quantity"]
                }
            }
        ]

    async def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Execute risk-specific tools"""
        if tool_name == "check_actor_reputation":
            return self._check_actor_reputation(tool_input, context)

        elif tool_name == "calculate_exposure":
            return self._calculate_exposure(tool_input)

        elif tool_name == "check_position_limits":
            return self._check_position_limits(tool_input, context)

        raise ValueError(f"Unknown tool: {tool_name}")

    def _check_actor_reputation(
        self,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Check actor reputation

        In production, queries:
        - Historical transaction database
        - Reputation scores
        - Default records
        - Community ratings
        """
        actor_address = tool_input["actor_address"]

        # Count actor's historical intents
        actor_intents = [
            i for i in context.available_intents
            if i.actor == actor_address
        ]

        # Simple reputation model
        intent_count = len(actor_intents)

        # Mock reputation score based on activity
        if intent_count == 0:
            reputation_score = 50  # New actor
        elif intent_count < 5:
            reputation_score = 60
        elif intent_count < 10:
            reputation_score = 75
        else:
            reputation_score = 85

        return {
            "actor_address": actor_address,
            "reputation_score": reputation_score,
            "intent_count": intent_count,
            "success_rate": 0.95,  # Mock
            "defaults": 0,
            "status": "good_standing",
            "member_since": "2024-01-01"
        }

    def _calculate_exposure(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate risk exposure

        Exposure = Price * Quantity * Volatility Factor
        """
        price = tool_input["price"]
        quantity = tool_input["quantity"]
        asset = tool_input["asset"]

        # Notional value
        notional = price * quantity

        # Volatility factors (higher for more volatile assets)
        volatility_factors = {
            "BTC": 1.5,
            "ETH": 1.8,
            "USDC": 1.0,
            "USD": 1.0
        }
        vol_factor = volatility_factors.get(asset, 2.0)

        # Risk exposure
        exposure = notional * vol_factor

        # Value at Risk (VaR) - simplified
        var_95 = exposure * 0.05  # 5% VaR

        return {
            "asset": asset,
            "notional_value": round(notional, 2),
            "risk_exposure": round(exposure, 2),
            "var_95": round(var_95, 2),
            "volatility_factor": vol_factor,
            "exposure_level": "low" if exposure < 50000 else "medium" if exposure < 200000 else "high"
        }

    def _check_position_limits(
        self,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Check position limits

        Ensures actors don't exceed max position sizes
        """
        actor_address = tool_input["actor_address"]
        asset = tool_input["asset"]
        quantity = tool_input["quantity"]

        # Default position limits
        position_limits = {
            "BTC": 10.0,
            "ETH": 100.0,
            "USDC": 1000000.0,
            "USD": 1000000.0
        }

        limit = position_limits.get(asset, 1.0)
        utilization = (quantity / limit) * 100

        return {
            "actor_address": actor_address,
            "asset": asset,
            "quantity": quantity,
            "limit": limit,
            "utilization_pct": round(utilization, 2),
            "within_limits": quantity <= limit,
            "remaining_capacity": round(max(0, limit - quantity), 4)
        }

    async def run(self, context: AgentContext) -> AgentResult:
        """
        Execute risk assessment

        Args:
            context: Agent context with match and market data

        Returns:
            AgentResult with risk assessment
        """
        try:
            input_intent = context.current_intent
            if not input_intent:
                return self.create_result(
                    success=False,
                    output={},
                    error="No input intent provided"
                )

            logger.info(f"Risk agent assessing intent {input_intent.intent_id}")

            # Get market data from previous agent
            market_data = None
            market_agent_result = context.previous_results.get("market_agent")
            if market_agent_result:
                market_data = market_agent_result.output.get("market_data")

            # Build risk assessment prompt
            prompt = self._build_risk_prompt(input_intent, context, market_data)

            # Call LLM with tools
            response = await self.call_llm(
                prompt=prompt,
                context=context,
                use_tools=True,
                temperature=0.2  # Low temperature for consistent risk decisions
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

            # Parse risk assessment
            output = self.parse_json_output(response)

            risk_assessment = output.get("risk_assessment", {})
            decision = output.get("decision", "review")
            conditions = output.get("conditions", [])
            reasoning = output.get("reasoning", "")
            confidence = output.get("confidence", 0.5)

            # Determine next agent based on decision
            if decision == "approve":
                next_agent = "settlement_agent"
            elif decision == "reject":
                next_agent = None  # End workflow
            else:
                next_agent = "settlement_agent"  # Proceed with conditions

            overall_score = risk_assessment.get("overall_score", 50)
            risk_level = risk_assessment.get("risk_level", "medium")

            logger.info(f"Risk assessment: {risk_level} ({overall_score}/100), decision: {decision}")

            return self.create_result(
                success=True,
                output={
                    "risk_assessment": risk_assessment,
                    "decision": decision,
                    "conditions": conditions,
                    "reasoning": reasoning
                },
                confidence=confidence,
                reasoning=reasoning,
                next_agent=next_agent
            )

        except Exception as e:
            logger.error(f"Risk agent error: {e}", exc_info=True)
            return self.create_result(
                success=False,
                output={},
                error=str(e)
            )

    def _build_risk_prompt(
        self,
        input_intent: Any,
        context: AgentContext,
        market_data: Dict[str, Any] = None
    ) -> str:
        """Build prompt for risk assessment"""
        prompt = f"""Assess the risk for this intent and its potential matches:

INPUT INTENT:
- Actor: {input_intent.actor}
- Asset: {input_intent.asset}
- Type: {input_intent.intent_type}
- Price: ${input_intent.price:,.2f}
- Quantity: {input_intent.quantity}
- Notional Value: ${input_intent.price * input_intent.quantity:,.2f}
"""

        # Add market data if available
        if market_data:
            prompt += f"""
MARKET CONDITIONS:
- Current Price: ${market_data.get('current_price', 0):,.2f}
- Volatility: {market_data.get('volatility', 0)}%
- Bid-Ask Spread: {market_data.get('bid_ask_spread', 0)}%
- Sentiment: {market_data.get('market_sentiment', 'unknown')}
"""

        # Add match information
        matching_result = context.previous_results.get("matching_agent")
        if matching_result and matching_result.output.get("matches"):
            matches = matching_result.output["matches"]
            prompt += f"\nPOTENTIAL MATCHES: {len(matches)}\n"
            for match in matches[:2]:
                prompt += f"- Settlement: ${match['settlement_price']:,.2f} x {match['settlement_quantity']}\n"
                prompt += f"  Match Score: {match['match_score']}\n"

        prompt += """
Use available tools to assess:
1. Actor reputation for all parties
2. Position exposure and limits
3. Overall risk profile

Provide a comprehensive risk assessment with your recommendation."""

        return prompt

    def _format_tool_results(self, tool_results: List[Dict[str, Any]]) -> str:
        """Format tool results"""
        results_str = "Risk assessment data gathered:\n"
        for result in tool_results:
            if result["success"]:
                results_str += f"- {result['tool_name']}: {json.dumps(result['result'], indent=2)}\n"
            else:
                results_str += f"- {result['tool_name']}: Error - {result['error']}\n"
        results_str += "\nProvide final risk assessment in JSON format."
        return results_str


# Testing
if __name__ == "__main__":
    import asyncio
    from services.langgraph import IntentData

    logging.basicConfig(level=logging.INFO)

    async def test_risk_agent():
        """Test risk agent"""
        print("\n=== Testing Risk Agent ===\n")

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
            request_id="risk-test-001"
        )

        agent = RiskAgent()
        print(f"Agent: {agent.name}")
        print(f"Tools: {len(agent.get_tools())}")

        # Test tools
        print("\n🔧 Testing reputation check:")
        rep = agent._check_actor_reputation({"actor_address": "0xBuyer1"}, context)
        print(f"Reputation score: {rep['reputation_score']}")

        print("\n🔧 Testing exposure calculation:")
        exp = agent._calculate_exposure({"price": 10100, "quantity": 1.0, "asset": "BTC"})
        print(f"Notional: ${exp['notional_value']:,.2f}")
        print(f"Risk exposure: ${exp['risk_exposure']:,.2f}")
        print(f"VaR 95%: ${exp['var_95']:,.2f}")

        print("\n🔧 Testing position limits:")
        limits = agent._check_position_limits({"actor_address": "0xBuyer1", "asset": "BTC", "quantity": 1.0}, context)
        print(f"Within limits: {limits['within_limits']}")
        print(f"Utilization: {limits['utilization_pct']}%")

        print("\n✅ Risk agent tools working correctly")

    asyncio.run(test_risk_agent())
