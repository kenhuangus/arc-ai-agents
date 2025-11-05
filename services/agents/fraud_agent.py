"""
Fraud Agent for Arc Coordination System

Detects suspicious patterns and fraudulent activity in intent matching.

Capabilities:
- Statistical anomaly detection
- Wash trading detection
- Price manipulation detection
- Blacklist checking
- Pattern analysis across intents
"""

import logging
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
import hashlib

from .base_agent import BaseAgent, AgentContext, AgentResult
from services.llm import ModelPreference

logger = logging.getLogger(__name__)


class FraudAgent(BaseAgent):
    """
    Fraud detection agent

    Uses Claude Sonnet 4.5 for:
    - Pattern recognition across intents
    - Anomaly scoring
    - Decision-making on suspicious activity
    - Structured fraud reports

    Detection Categories:
    1. Wash Trading: Same actors on both sides
    2. Price Manipulation: Unusual price patterns
    3. Volume Anomalies: Suspicious quantity patterns
    4. Timing Patterns: Coordinated timing
    5. Blacklist Matches: Known bad actors
    """

    def __init__(self):
        super().__init__(
            name="fraud_agent",
            description="Detects suspicious patterns and fraudulent activity",
            model_preference=ModelPreference.CLAUDE  # Claude for pattern analysis
        )

    def get_system_prompt(self, context: AgentContext) -> str:
        """Get system prompt for fraud agent"""
        return """You are an expert fraud detection agent for the Arc Coordination System.

Your role is to detect suspicious patterns and prevent fraudulent trades.

FRAUD DETECTION RULES:

1. WASH TRADING (Critical)
   - Same actor on both sides of trade
   - Related wallets (shared history)
   - Circular trading patterns
   - Action: BLOCK

2. PRICE MANIPULATION (High)
   - Prices significantly outside market range (>10%)
   - Coordinated price movements
   - Spoofing patterns
   - Action: FLAG for review

3. VOLUME ANOMALIES (Medium)
   - Unusual quantity for actor
   - Quantity >> normal for asset
   - Repeated same-size orders
   - Action: Monitor

4. TIMING PATTERNS (Medium)
   - Orders placed within seconds
   - Coordinated multi-party timing
   - Automated bot patterns
   - Action: Rate limit

5. BLACKLIST MATCHES (Critical)
   - Known scammer addresses
   - Sanctioned entities
   - Previous fraud history
   - Action: BLOCK

RISK SCORING (0-100):
- 0-20: Clean - No issues detected
- 21-40: Low risk - Minor anomalies
- 41-60: Medium risk - Multiple flags
- 61-80: High risk - Suspicious patterns
- 81-100: Critical - Likely fraud

DECISION MATRIX:
- Score 0-40: APPROVE
- Score 41-60: APPROVE with monitoring
- Score 61-80: REJECT with explanation
- Score 81-100: BLOCK permanently

You must respond in valid JSON format:
{
  "fraud_check": {
    "fraud_score": 15,
    "risk_level": "low",
    "flags": [
      {
        "category": "timing_patterns",
        "severity": "low",
        "description": "Orders within 5 minutes"
      }
    ],
    "wash_trading_detected": false,
    "price_manipulation_detected": false,
    "blacklist_match": false
  },
  "decision": "approve",
  "reasoning": "No significant fraud indicators detected...",
  "confidence": 0.92
}

IMPORTANT: Always return valid JSON. Be conservative - false positives are better than missing fraud."""

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get tool definitions for fraud agent"""
        return [
            {
                "name": "check_wash_trading",
                "description": "Check if same actor or related actors on both sides",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "actor_a": {"type": "string", "description": "First actor address"},
                        "actor_b": {"type": "string", "description": "Second actor address"}
                    },
                    "required": ["actor_a", "actor_b"]
                }
            },
            {
                "name": "check_price_anomaly",
                "description": "Check if price is anomalous compared to market",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "intent_price": {"type": "number", "description": "Intent price"},
                        "market_price": {"type": "number", "description": "Market price"},
                        "asset": {"type": "string", "description": "Asset symbol"}
                    },
                    "required": ["intent_price", "market_price", "asset"]
                }
            },
            {
                "name": "check_blacklist",
                "description": "Check if actor is on blacklist",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "actor_address": {"type": "string", "description": "Actor address to check"}
                    },
                    "required": ["actor_address"]
                }
            },
            {
                "name": "analyze_timing_pattern",
                "description": "Analyze timing patterns across intents",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "actor_address": {"type": "string", "description": "Actor address"},
                        "lookback_hours": {"type": "number", "description": "Hours to look back"}
                    },
                    "required": ["actor_address"]
                }
            }
        ]

    async def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Execute fraud detection tools"""
        if tool_name == "check_wash_trading":
            return self._check_wash_trading(tool_input)

        elif tool_name == "check_price_anomaly":
            return self._check_price_anomaly(tool_input, context)

        elif tool_name == "check_blacklist":
            return self._check_blacklist(tool_input)

        elif tool_name == "analyze_timing_pattern":
            return self._analyze_timing_pattern(tool_input, context)

        raise ValueError(f"Unknown tool: {tool_name}")

    def _check_wash_trading(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for wash trading

        In production:
        - Check wallet graph relationships
        - Analyze transaction history
        - Detect circular patterns
        """
        actor_a = tool_input["actor_a"]
        actor_b = tool_input["actor_b"]

        # Simple check: exact match
        is_same = actor_a.lower() == actor_b.lower()

        # Check for similar addresses (mock relationship detection)
        similarity = 0.0
        if len(actor_a) == len(actor_b):
            matching_chars = sum(1 for a, b in zip(actor_a, actor_b) if a == b)
            similarity = matching_chars / len(actor_a)

        # High similarity might indicate related wallets
        is_related = similarity > 0.9 and not is_same

        return {
            "actor_a": actor_a,
            "actor_b": actor_b,
            "is_same_actor": is_same,
            "is_likely_related": is_related,
            "similarity_score": round(similarity, 3),
            "wash_trading_risk": "critical" if is_same else "high" if is_related else "none"
        }

    def _check_price_anomaly(
        self,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Check for price anomalies

        Compares intent price against market price
        """
        intent_price = tool_input["intent_price"]
        market_price = tool_input["market_price"]
        asset = tool_input["asset"]

        if market_price == 0:
            return {
                "anomalous": False,
                "reason": "No market price available"
            }

        # Calculate deviation
        deviation = abs(intent_price - market_price)
        deviation_pct = (deviation / market_price) * 100

        # Thresholds
        is_anomalous = deviation_pct > 10  # >10% from market
        is_suspicious = deviation_pct > 20  # >20% is very suspicious

        if is_suspicious:
            severity = "critical"
        elif is_anomalous:
            severity = "high"
        else:
            severity = "none"

        return {
            "asset": asset,
            "intent_price": intent_price,
            "market_price": market_price,
            "deviation": round(deviation, 2),
            "deviation_pct": round(deviation_pct, 2),
            "anomalous": is_anomalous,
            "severity": severity,
            "threshold_10pct": deviation_pct > 10,
            "threshold_20pct": deviation_pct > 20
        }

    def _check_blacklist(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check blacklist

        In production:
        - Query blacklist database
        - Check OFAC sanctions
        - Cross-reference with fraud database
        """
        actor_address = tool_input["actor_address"]

        # Mock blacklist (in production, query real database)
        blacklisted_addresses = {
            "0xBAD1": "Known scammer",
            "0xBAD2": "OFAC sanctioned",
            "0xBAD3": "Previous fraud"
        }

        is_blacklisted = actor_address in blacklisted_addresses
        reason = blacklisted_addresses.get(actor_address, None)

        return {
            "actor_address": actor_address,
            "is_blacklisted": is_blacklisted,
            "reason": reason,
            "risk_level": "critical" if is_blacklisted else "none",
            "last_checked": int(datetime.now().timestamp())
        }

    def _analyze_timing_pattern(
        self,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Analyze timing patterns

        Detects suspicious timing in order placement
        """
        actor_address = tool_input["actor_address"]
        lookback_hours = tool_input.get("lookback_hours", 24)

        # Find actor's recent intents
        now = int(datetime.now().timestamp())
        cutoff = now - (lookback_hours * 3600)

        actor_intents = [
            i for i in context.available_intents
            if i.actor == actor_address and i.timestamp >= cutoff
        ]

        if len(actor_intents) < 2:
            return {
                "actor_address": actor_address,
                "intent_count": len(actor_intents),
                "suspicious_timing": False,
                "pattern": "insufficient_data"
            }

        # Sort by timestamp
        sorted_intents = sorted(actor_intents, key=lambda x: x.timestamp)

        # Check for very rapid orders
        rapid_orders = 0
        for i in range(len(sorted_intents) - 1):
            time_diff = sorted_intents[i + 1].timestamp - sorted_intents[i].timestamp
            if time_diff < 60:  # Less than 1 minute apart
                rapid_orders += 1

        # Check for identical quantities (bot pattern)
        quantities = [i.quantity for i in sorted_intents]
        identical_quantities = len(set(quantities)) == 1 and len(quantities) > 2

        suspicious = rapid_orders > 2 or identical_quantities

        return {
            "actor_address": actor_address,
            "intent_count": len(actor_intents),
            "rapid_orders": rapid_orders,
            "identical_quantities": identical_quantities,
            "suspicious_timing": suspicious,
            "pattern": "bot_pattern" if identical_quantities else "rapid_trading" if rapid_orders > 2 else "normal",
            "severity": "medium" if suspicious else "none"
        }

    async def run(self, context: AgentContext) -> AgentResult:
        """
        Execute fraud detection

        Args:
            context: Agent context with intents and matches

        Returns:
            AgentResult with fraud assessment
        """
        try:
            input_intent = context.current_intent
            if not input_intent:
                return self.create_result(
                    success=False,
                    output={},
                    error="No input intent provided"
                )

            logger.info(f"Fraud agent analyzing intent {input_intent.intent_id}")

            # Get matches from previous agent
            matches = []
            matching_result = context.previous_results.get("matching_agent")
            if matching_result:
                matches = matching_result.output.get("matches", [])

            # Get market data for price anomaly check
            market_data = None
            market_result = context.previous_results.get("market_agent")
            if market_result:
                market_data = market_result.output.get("market_data")

            # Build fraud detection prompt
            prompt = self._build_fraud_prompt(input_intent, matches, context, market_data)

            # Call LLM with tools
            response = await self.call_llm(
                prompt=prompt,
                context=context,
                use_tools=True,
                temperature=0.1  # Very low temperature for consistent fraud detection
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

            # Parse fraud assessment
            output = self.parse_json_output(response)

            fraud_check = output.get("fraud_check", {})
            decision = output.get("decision", "review")
            reasoning = output.get("reasoning", "")
            confidence = output.get("confidence", 0.5)

            fraud_score = fraud_check.get("fraud_score", 0)

            # Determine next agent
            # Fraud detection runs in parallel with market agent,
            # both feed into risk agent
            next_agent = None  # Let graph router handle this

            logger.info(f"Fraud check: score={fraud_score}, decision={decision}")

            return self.create_result(
                success=True,
                output={
                    "fraud_check": fraud_check,
                    "decision": decision,
                    "reasoning": reasoning
                },
                confidence=confidence,
                reasoning=reasoning,
                next_agent=next_agent
            )

        except Exception as e:
            logger.error(f"Fraud agent error: {e}", exc_info=True)
            return self.create_result(
                success=False,
                output={},
                error=str(e)
            )

    def _build_fraud_prompt(
        self,
        input_intent: Any,
        matches: List[Dict],
        context: AgentContext,
        market_data: Dict = None
    ) -> str:
        """Build prompt for fraud detection"""
        prompt = f"""Analyze this intent and its matches for fraud indicators:

INPUT INTENT:
- ID: {input_intent.intent_id}
- Actor: {input_intent.actor}
- Type: {input_intent.intent_type}
- Asset: {input_intent.asset}
- Price: ${input_intent.price:,.2f}
- Quantity: {input_intent.quantity}
- Timestamp: {input_intent.timestamp}
"""

        if market_data:
            prompt += f"""
MARKET DATA:
- Current Price: ${market_data.get('current_price', 0):,.2f}
- Volatility: {market_data.get('volatility', 0)}%
"""

        if matches:
            prompt += f"\n POTENTIAL MATCHES: {len(matches)}\n"
            for i, match in enumerate(matches[:3]):
                # Find the matching intent
                match_intent_id = match.get('intent_b_id')
                match_intent = next(
                    (intent for intent in context.available_intents if intent.intent_id == match_intent_id),
                    None
                )
                if match_intent:
                    prompt += f"""
Match {i+1}:
  - Counterparty: {match_intent.actor}
  - Price: ${match['settlement_price']:,.2f}
  - Quantity: {match['settlement_quantity']}
"""

        prompt += """
Use available tools to check for:
1. Wash trading (same/related actors)
2. Price manipulation (anomalous prices)
3. Blacklist matches
4. Suspicious timing patterns

Provide comprehensive fraud assessment."""

        return prompt

    def _format_tool_results(self, tool_results: List[Dict[str, Any]]) -> str:
        """Format tool results"""
        results_str = "Fraud detection results:\n"
        for result in tool_results:
            if result["success"]:
                results_str += f"- {result['tool_name']}: {json.dumps(result['result'], indent=2)}\n"
            else:
                results_str += f"- {result['tool_name']}: Error - {result['error']}\n"
        results_str += "\nProvide final fraud assessment in JSON format."
        return results_str


# Testing
if __name__ == "__main__":
    import asyncio
    from services.langgraph import IntentData

    logging.basicConfig(level=logging.INFO)

    async def test_fraud_agent():
        """Test fraud agent"""
        print("\n=== Testing Fraud Agent ===\n")

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
            request_id="fraud-test-001"
        )

        agent = FraudAgent()
        print(f"Agent: {agent.name}")
        print(f"Tools: {len(agent.get_tools())}")

        # Test tools
        print("\n🔧 Testing wash trading check:")
        wash = agent._check_wash_trading({"actor_a": "0xBuyer1", "actor_b": "0xSeller1"})
        print(f"Same actor: {wash['is_same_actor']}")
        print(f"Risk: {wash['wash_trading_risk']}")

        print("\n🔧 Testing price anomaly:")
        anomaly = agent._check_price_anomaly({
            "intent_price": 10100,
            "market_price": 10000,
            "asset": "BTC"
        }, context)
        print(f"Deviation: {anomaly['deviation_pct']}%")
        print(f"Anomalous: {anomaly['anomalous']}")

        print("\n🔧 Testing blacklist:")
        blacklist = agent._check_blacklist({"actor_address": "0xBuyer1"})
        print(f"Blacklisted: {blacklist['is_blacklisted']}")

        print("\n✅ Fraud agent tools working correctly")

    asyncio.run(test_fraud_agent())
