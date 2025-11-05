"""
Matching Agent for Arc Coordination System

Finds optimal matches between intents using AI-powered analysis.

Capabilities:
- Analyze intent compatibility (bid/ask, price, quantity)
- Score matches based on multiple criteria
- Use LLM for complex matching logic
- Handle partial matches and spread calculations
- Prioritize best matches with confidence scores
"""

import logging
import json
from typing import List, Dict, Any
from datetime import datetime
import hashlib

from .base_agent import BaseAgent, AgentContext, AgentResult
from services.llm import ModelPreference
from services.langgraph.state import IntentData, MatchResult

logger = logging.getLogger(__name__)


class MatchingAgent(BaseAgent):
    """
    Intelligent intent matching agent

    Uses Claude Sonnet 4.5 for:
    - Complex matching logic with multiple criteria
    - Confidence scoring
    - Natural language reasoning about matches
    - Handling edge cases (partial fills, spread analysis)

    Matching Criteria:
    1. Type compatibility (bid matches ask, vice versa)
    2. Price overlap (bid >= ask)
    3. Quantity compatibility
    4. Timing (valid_until constraints)
    5. Settlement asset compatibility
    6. AP2 mandate compatibility
    """

    def __init__(self):
        super().__init__(
            name="matching_agent",
            description="Finds optimal intent matches using AI-powered analysis",
            model_preference=ModelPreference.CLAUDE  # Claude is best for structured reasoning
        )

    def get_system_prompt(self, context: AgentContext) -> str:
        """Get system prompt for matching agent"""
        return """You are an expert intent matching agent for the Arc Coordination System.

Your role is to find optimal matches between buyer and seller intents.

MATCHING RULES:
1. Type Compatibility: Bids can only match with asks, and vice versa
2. Price Compatibility: Bid price must be >= ask price for a valid match
3. Quantity: Match as much quantity as possible (partial matches allowed)
4. Timing: Both intents must be active and valid
5. Settlement: Settlement assets should be compatible
6. Spread: Calculate the spread (bid price - ask price)
7. Settlement Price: Use midpoint for matched price

SCORING CRITERIA (0.0 to 1.0):
- Perfect price match: 1.0
- Small spread (<1%): 0.9-1.0
- Medium spread (1-5%): 0.7-0.9
- Large spread (5-10%): 0.5-0.7
- Very large spread (>10%): 0.3-0.5

CONFIDENCE CRITERIA:
- Both intents recently created: High confidence
- Large quantity match: High confidence
- Small spread: High confidence
- Mismatched settlement assets: Lower confidence
- Near expiration: Lower confidence

You must respond in valid JSON format with this exact structure:
{
  "matches": [
    {
      "intent_b_id": "0x...",
      "match_score": 0.95,
      "confidence": 0.90,
      "spread": 100.0,
      "settlement_price": 10050.0,
      "settlement_quantity": 1.0,
      "reasoning": "Excellent match: prices very close, full quantity match"
    }
  ],
  "next_agent": "market_agent" or null
}

IMPORTANT: Always return valid JSON. No markdown, no code blocks, just pure JSON."""

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get tool definitions for matching agent"""
        return [
            {
                "name": "calculate_match_score",
                "description": "Calculate match score between two intents based on price, quantity, and timing",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "intent_a_price": {"type": "number", "description": "Price of first intent"},
                        "intent_b_price": {"type": "number", "description": "Price of second intent"},
                        "intent_a_type": {"type": "string", "description": "Type: bid or ask"},
                        "intent_b_type": {"type": "string", "description": "Type: bid or ask"}
                    },
                    "required": ["intent_a_price", "intent_b_price", "intent_a_type", "intent_b_type"]
                }
            },
            {
                "name": "filter_compatible_intents",
                "description": "Filter available intents for compatibility with input intent",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "input_type": {"type": "string", "description": "Type of input intent: bid or ask"},
                        "input_asset": {"type": "string", "description": "Asset symbol"}
                    },
                    "required": ["input_type", "input_asset"]
                }
            }
        ]

    async def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Execute matching-specific tools"""
        if tool_name == "calculate_match_score":
            return self._calculate_match_score(tool_input)

        elif tool_name == "filter_compatible_intents":
            return await self._filter_compatible_intents(tool_input, context)

        raise ValueError(f"Unknown tool: {tool_name}")

    def _calculate_match_score(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate match score between two intents"""
        price_a = tool_input["intent_a_price"]
        price_b = tool_input["intent_b_price"]
        type_a = tool_input["intent_a_type"]
        type_b = tool_input["intent_b_type"]

        # Check type compatibility
        if type_a == type_b:
            return {"match_score": 0.0, "reason": "Same type - no match"}

        # Determine bid and ask
        if type_a == "bid":
            bid_price = price_a
            ask_price = price_b
        else:
            bid_price = price_b
            ask_price = price_a

        # Check price compatibility
        if bid_price < ask_price:
            return {"match_score": 0.0, "reason": "Bid below ask - no match"}

        # Calculate spread and score
        spread = bid_price - ask_price
        spread_pct = (spread / ask_price) * 100 if ask_price > 0 else 100

        if spread_pct < 1:
            score = 1.0
        elif spread_pct < 5:
            score = 0.9 - (spread_pct - 1) * 0.05
        elif spread_pct < 10:
            score = 0.7 - (spread_pct - 5) * 0.04
        else:
            score = max(0.3, 0.5 - (spread_pct - 10) * 0.02)

        return {
            "match_score": round(score, 3),
            "spread": spread,
            "spread_pct": round(spread_pct, 2),
            "bid_price": bid_price,
            "ask_price": ask_price,
            "settlement_price": (bid_price + ask_price) / 2
        }

    async def _filter_compatible_intents(
        self,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Filter available intents for compatibility"""
        input_type = tool_input["input_type"]
        input_asset = tool_input["input_asset"]

        # Determine opposite type
        opposite_type = "ask" if input_type == "bid" else "bid"

        # Filter from context
        compatible = []
        for intent in context.available_intents:
            if intent.intent_type == opposite_type and intent.asset == input_asset and intent.is_active:
                compatible.append({
                    "intent_id": intent.intent_id,
                    "price": intent.price,
                    "quantity": intent.quantity,
                    "timestamp": intent.timestamp
                })

        return {
            "compatible_count": len(compatible),
            "compatible_intents": compatible[:10]  # Limit to top 10
        }

    async def run(self, context: AgentContext) -> AgentResult:
        """
        Execute matching agent logic

        Args:
            context: Agent context with input intent and available intents

        Returns:
            AgentResult with matches found
        """
        try:
            input_intent = context.current_intent
            if not input_intent:
                return self.create_result(
                    success=False,
                    output={},
                    error="No input intent provided"
                )

            logger.info(f"Matching agent analyzing intent {input_intent.intent_id}")

            # Build prompt for LLM
            prompt = self._build_matching_prompt(input_intent, context.available_intents)

            # Call LLM with tools
            response = await self.call_llm(
                prompt=prompt,
                context=context,
                use_tools=True,
                temperature=0.3  # Lower temperature for more consistent matching
            )

            # Handle tool calls if LLM requested them
            if response.get("stop_reason") == "tool_use":
                tool_results = await self.handle_tool_calls(response, context)

                # Continue conversation with tool results
                tool_result_message = self._format_tool_results(tool_results)
                response = await self.call_llm(
                    prompt=tool_result_message,
                    context=context,
                    use_tools=False
                )

            # Parse matches from response
            output = self.parse_json_output(response)

            # Convert to MatchResult objects
            matches = []
            for match_data in output.get("matches", []):
                match = MatchResult(
                    match_id=self._generate_match_id(input_intent.intent_id, match_data["intent_b_id"]),
                    intent_a_id=input_intent.intent_id,
                    intent_b_id=match_data["intent_b_id"],
                    match_score=match_data["match_score"],
                    confidence=match_data["confidence"],
                    spread=match_data["spread"],
                    settlement_price=match_data["settlement_price"],
                    settlement_quantity=match_data["settlement_quantity"],
                    reasoning=match_data["reasoning"]
                )
                matches.append(match)

            next_agent = output.get("next_agent")

            logger.info(f"Found {len(matches)} matches for intent {input_intent.intent_id}")

            return self.create_result(
                success=True,
                output={
                    "matches": [m.to_dict() for m in matches],
                    "match_count": len(matches)
                },
                confidence=max([m.confidence for m in matches]) if matches else 0.0,
                reasoning=f"Analyzed {len(context.available_intents)} intents, found {len(matches)} matches",
                next_agent=next_agent if matches else "liquidity_agent"
            )

        except Exception as e:
            logger.error(f"Matching agent error: {e}", exc_info=True)
            return self.create_result(
                success=False,
                output={},
                error=str(e)
            )

    def _build_matching_prompt(
        self,
        input_intent: IntentData,
        available_intents: List[IntentData]
    ) -> str:
        """Build prompt for LLM matching analysis"""
        # Limit to reasonable number of intents
        limited_intents = available_intents[:20]

        prompt = f"""Analyze this intent and find the best matches:

INPUT INTENT:
- ID: {input_intent.intent_id}
- Type: {input_intent.intent_type}
- Asset: {input_intent.asset}
- Price: ${input_intent.price:,.2f}
- Quantity: {input_intent.quantity}
- Settlement Asset: {input_intent.settlement_asset}
- Valid Until: {input_intent.valid_until}

AVAILABLE INTENTS ({len(limited_intents)} total):
"""

        for intent in limited_intents:
            prompt += f"""
- ID: {intent.intent_id}
  Type: {intent.intent_type}
  Price: ${intent.price:,.2f}
  Quantity: {intent.quantity}
  Asset: {intent.asset}
  Settlement: {intent.settlement_asset}
"""

        prompt += """
Analyze these intents and return the top matches in JSON format.
Use the calculate_match_score tool if needed.
"""

        return prompt

    def _format_tool_results(self, tool_results: List[Dict[str, Any]]) -> str:
        """Format tool results for continuation"""
        results_str = "Tool execution results:\n"
        for result in tool_results:
            if result["success"]:
                results_str += f"- {result['tool_name']}: {json.dumps(result['result'])}\n"
            else:
                results_str += f"- {result['tool_name']}: Error - {result['error']}\n"
        results_str += "\nNow provide the final JSON response with matches."
        return results_str

    def _generate_match_id(self, intent_a_id: str, intent_b_id: str) -> str:
        """Generate unique match ID"""
        combined = f"{intent_a_id}:{intent_b_id}"
        return "0x" + hashlib.sha256(combined.encode()).hexdigest()[:16]


# Testing
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def test_matching_agent():
        """Test matching agent"""
        print("\n=== Testing Matching Agent ===\n")

        # Create test intents
        bid_intent = IntentData(
            intent_id="0xBID123",
            intent_hash="0xbid",
            actor="0xBuyer",
            intent_type="bid",
            price=10100.0,
            quantity=1.0,
            asset="BTC",
            settlement_asset="USD",
            timestamp=int(datetime.now().timestamp()),
            valid_until=int(datetime.now().timestamp()) + 86400,
            ap2_mandate_id="0xMandate1",
            is_active=True
        )

        ask_intent = IntentData(
            intent_id="0xASK456",
            intent_hash="0xask",
            actor="0xSeller",
            intent_type="ask",
            price=10000.0,
            quantity=1.0,
            asset="BTC",
            settlement_asset="USD",
            timestamp=int(datetime.now().timestamp()),
            valid_until=int(datetime.now().timestamp()) + 86400,
            ap2_mandate_id="0xMandate2",
            is_active=True
        )

        # Create context
        context = AgentContext(
            current_intent=bid_intent,
            available_intents=[ask_intent],
            request_id="test-match-001"
        )

        # Run agent
        agent = MatchingAgent()
        result = await agent.run(context)

        print(f"Success: {result.success}")
        print(f"Matches found: {result.output.get('match_count', 0)}")
        print(f"Confidence: {result.confidence}")
        print(f"Reasoning: {result.reasoning}")

        if result.success:
            print("\n✅ Matching agent test passed")
        else:
            print(f"\n❌ Error: {result.error}")

    print("Matching agent created")
    print("To test with actual API keys: python -m services.agents.matching_agent")
    # asyncio.run(test_matching_agent())
