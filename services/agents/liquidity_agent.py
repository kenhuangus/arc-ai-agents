"""
Liquidity Agent for Arc Coordination System

Provides market making and liquidity when no intent matches are found.

Capabilities:
- Generate market maker quotes
- Dynamic pricing based on inventory
- Risk-adjusted quote generation
- Liquidity provision strategy
- Inventory management
"""

import logging
import json
from typing import List, Dict, Any
from datetime import datetime
import random

from .base_agent import BaseAgent, AgentContext, AgentResult
from services.llm import ModelPreference

logger = logging.getLogger(__name__)


class LiquidityAgent(BaseAgent):
    """
    Liquidity and market making agent

    Uses Gemini 2.5 Pro for:
    - Market analysis with historical data
    - Inventory optimization
    - Dynamic pricing strategies
    - Multi-asset portfolio analysis

    Market Making Strategy:
    1. Assess current inventory position
    2. Analyze market conditions
    3. Calculate risk-adjusted spread
    4. Generate two-sided quote
    5. Monitor and adjust
    """

    def __init__(self):
        super().__init__(
            name="liquidity_agent",
            description="Provides market making and liquidity",
            model_preference=ModelPreference.GEMINI  # Gemini for portfolio analysis
        )

    def get_system_prompt(self, context: AgentContext) -> str:
        """Get system prompt for liquidity agent"""
        return """You are an expert market making agent for the Arc Coordination System.

Your role is to provide liquidity when no natural matches exist between intents.

MARKET MAKING FRAMEWORK:

1. INVENTORY MANAGEMENT
   - Target: Neutral position (50% long, 50% short)
   - Max position: ±20% of capital
   - Rebalance when >10% skew

2. PRICING STRATEGY
   - Base spread: Market volatility × 2
   - Inventory skew: Adjust prices to rebalance
   - Volume discount: Tighter spreads for larger size
   - Risk premium: Wider spreads in volatile markets

3. SPREAD CALCULATION
   - Low volatility (<2%): 0.5-1% spread
   - Medium volatility (2-5%): 1-2% spread
   - High volatility (>5%): 2-4% spread
   - Add inventory skew adjustment

4. QUOTE GENERATION
   - Two-sided: Both bid and ask
   - Size-dependent: Price improves with quantity
   - Time-dependent: Tighten spreads during peak hours
   - Risk-adjusted: Wider spreads for risky assets

5. RISK MANAGEMENT
   - Max position per asset: $100,000
   - Max total exposure: $500,000
   - Stop-loss: 5% adverse move
   - Hedge positions: Use correlated assets

QUOTE STRUCTURE:
```
{
  "liquidity_quote": {
    "asset": "BTC",
    "bid": {
      "price": 10000,
      "quantity": 1.0,
      "valid_until": 1234567890
    },
    "ask": {
      "price": 10100,
      "quantity": 1.0,
      "valid_until": 1234567890
    },
    "spread_bps": 100,
    "mid_price": 10050,
    "inventory_position": {
      "current_btc": 0.5,
      "target_btc": 0.0,
      "skew": "long"
    }
  },
  "pricing_rationale": "Base spread 0.5% + 0.5% inventory adjustment",
  "confidence": 0.88,
  "execution_probability": 0.65
}
```

IMPORTANT: Always return valid JSON. Quotes must be executable."""

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get tool definitions for liquidity agent"""
        return [
            {
                "name": "calculate_quote",
                "description": "Calculate market maker quote for an asset",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "asset": {"type": "string", "description": "Asset symbol"},
                        "intent_type": {"type": "string", "description": "Original intent type: bid or ask"},
                        "quantity": {"type": "number", "description": "Desired quantity"},
                        "market_price": {"type": "number", "description": "Current market price"}
                    },
                    "required": ["asset", "intent_type", "quantity", "market_price"]
                }
            },
            {
                "name": "assess_inventory",
                "description": "Assess current inventory position",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "asset": {"type": "string", "description": "Asset symbol"}
                    },
                    "required": ["asset"]
                }
            },
            {
                "name": "calculate_spread",
                "description": "Calculate optimal spread based on volatility and inventory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "asset": {"type": "string", "description": "Asset symbol"},
                        "volatility": {"type": "number", "description": "Volatility percentage"},
                        "inventory_skew": {"type": "number", "description": "Inventory skew (-1 to 1)"}
                    },
                    "required": ["asset", "volatility"]
                }
            }
        ]

    async def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Execute liquidity tools"""
        if tool_name == "calculate_quote":
            return self._calculate_quote(tool_input, context)

        elif tool_name == "assess_inventory":
            return self._assess_inventory(tool_input, context)

        elif tool_name == "calculate_spread":
            return self._calculate_spread(tool_input)

        raise ValueError(f"Unknown tool: {tool_name}")

    def _calculate_quote(
        self,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Calculate market maker quote

        In production:
        - Query real-time market data
        - Check inventory positions
        - Calculate risk metrics
        - Generate executable quote
        """
        asset = tool_input["asset"]
        intent_type = tool_input["intent_type"]
        quantity = tool_input["quantity"]
        market_price = tool_input["market_price"]

        # Get inventory
        inventory = self._assess_inventory({"asset": asset}, context)
        inventory_skew = inventory["skew_pct"] / 100  # -1 to 1

        # Get volatility from context
        volatility = 2.5  # Default
        market_result = context.previous_results.get("market_agent")
        if market_result and market_result.output.get("market_data"):
            volatility = market_result.output["market_data"].get("volatility", 2.5)

        # Calculate spread
        spread_result = self._calculate_spread({
            "asset": asset,
            "volatility": volatility,
            "inventory_skew": inventory_skew
        })

        spread_pct = spread_result["spread_pct"]
        half_spread = market_price * (spread_pct / 200)  # Half spread on each side

        # Generate two-sided quote
        bid_price = market_price - half_spread
        ask_price = market_price + half_spread

        # Adjust for inventory skew
        if inventory_skew > 0:  # Long position, want to sell
            bid_price -= market_price * 0.001  # Reduce bid
            ask_price -= market_price * 0.001  # Reduce ask (more competitive)
        elif inventory_skew < 0:  # Short position, want to buy
            bid_price += market_price * 0.001  # Increase bid (more competitive)
            ask_price += market_price * 0.001  # Increase ask

        # Valid for 5 minutes
        valid_until = int(datetime.now().timestamp()) + 300

        return {
            "asset": asset,
            "market_price": market_price,
            "bid_price": round(bid_price, 2),
            "ask_price": round(ask_price, 2),
            "bid_quantity": quantity,
            "ask_quantity": quantity,
            "spread_bps": int(spread_pct * 100),
            "mid_price": market_price,
            "valid_until": valid_until,
            "inventory_adjusted": abs(inventory_skew) > 0.05,
            "quote_type": "two_sided"
        }

    def _assess_inventory(
        self,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Assess inventory position

        In production:
        - Query position database
        - Calculate net position
        - Determine skew vs target
        """
        asset = tool_input["asset"]

        # Mock inventory (in production, query real positions)
        # Simulate random inventory between -10 and +10 units
        current_position = random.uniform(-5, 5)
        target_position = 0.0  # Market maker wants neutral

        skew = current_position - target_position
        skew_pct = (skew / 10) * 100 if abs(skew) > 0 else 0  # -100 to +100

        position_limit = 10.0
        utilization_pct = (abs(current_position) / position_limit) * 100

        return {
            "asset": asset,
            "current_position": round(current_position, 4),
            "target_position": target_position,
            "skew": round(skew, 4),
            "skew_pct": round(skew_pct, 2),
            "position_limit": position_limit,
            "utilization_pct": round(utilization_pct, 2),
            "needs_rebalancing": abs(skew_pct) > 10,
            "risk_level": "high" if utilization_pct > 80 else "medium" if utilization_pct > 50 else "low"
        }

    def _calculate_spread(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate optimal spread

        Spread = Base Spread + Volatility Premium + Inventory Adjustment
        """
        asset = tool_input["asset"]
        volatility = tool_input["volatility"]
        inventory_skew = tool_input.get("inventory_skew", 0.0)

        # Base spread (minimum profitable spread)
        base_spread_pct = 0.3

        # Volatility premium
        if volatility < 2:
            vol_premium = 0.2
        elif volatility < 5:
            vol_premium = 0.5
        else:
            vol_premium = 1.0

        # Inventory adjustment
        inventory_adjustment = abs(inventory_skew) * 0.5  # Up to 0.5% for max skew

        # Total spread
        total_spread_pct = base_spread_pct + vol_premium + inventory_adjustment

        return {
            "asset": asset,
            "spread_pct": round(total_spread_pct, 3),
            "base_spread": base_spread_pct,
            "volatility_premium": vol_premium,
            "inventory_adjustment": round(inventory_adjustment, 3),
            "spread_bps": int(total_spread_pct * 100),
            "competitive": total_spread_pct < 1.0
        }

    async def run(self, context: AgentContext) -> AgentResult:
        """
        Execute liquidity provision

        Args:
            context: Agent context with unmatched intent

        Returns:
            AgentResult with liquidity quote
        """
        try:
            input_intent = context.current_intent
            if not input_intent:
                return self.create_result(
                    success=False,
                    output={},
                    error="No input intent provided"
                )

            logger.info(f"Liquidity agent providing quote for intent {input_intent.intent_id}")

            # Get market data
            market_price = input_intent.price  # Fallback to intent price
            market_result = context.previous_results.get("market_agent")
            if market_result and market_result.output.get("market_data"):
                market_price = market_result.output["market_data"].get("current_price", input_intent.price)

            # Build liquidity prompt
            prompt = self._build_liquidity_prompt(input_intent, market_price, context)

            # Call LLM with tools
            response = await self.call_llm(
                prompt=prompt,
                context=context,
                use_tools=True,
                temperature=0.4  # Moderate creativity for pricing
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

            # Parse liquidity quote
            output = self.parse_json_output(response)

            liquidity_quote = output.get("liquidity_quote", {})
            pricing_rationale = output.get("pricing_rationale", "")
            confidence = output.get("confidence", 0.5)
            execution_probability = output.get("execution_probability", 0.5)

            logger.info(f"Liquidity quote generated: spread={liquidity_quote.get('spread_bps', 0)}bps")

            return self.create_result(
                success=True,
                output={
                    "liquidity_quote": liquidity_quote,
                    "pricing_rationale": pricing_rationale,
                    "execution_probability": execution_probability
                },
                confidence=confidence,
                reasoning=pricing_rationale,
                next_agent=None  # End of workflow
            )

        except Exception as e:
            logger.error(f"Liquidity agent error: {e}", exc_info=True)
            return self.create_result(
                success=False,
                output={},
                error=str(e)
            )

    def _build_liquidity_prompt(
        self,
        input_intent: Any,
        market_price: float,
        context: AgentContext
    ) -> str:
        """Build prompt for liquidity quote"""
        prompt = f"""Generate a market maker quote for this unmatched intent:

INPUT INTENT (No Natural Match Found):
- Type: {input_intent.intent_type}
- Asset: {input_intent.asset}
- Quantity: {input_intent.quantity}
- User Price: ${input_intent.price:,.2f}
- Market Price: ${market_price:,.2f}
"""

        # Add market data if available
        market_result = context.previous_results.get("market_agent")
        if market_result and market_result.output.get("market_data"):
            market_data = market_result.output["market_data"]
            prompt += f"""
MARKET CONDITIONS:
- Volatility: {market_data.get('volatility', 0)}%
- Sentiment: {market_data.get('market_sentiment', 'neutral')}
- Bid-Ask Spread: {market_data.get('bid_ask_spread', 0)}%
"""

        prompt += f"""
LIQUIDITY PROVIDER INFO:
- Total intents in pool: {len(context.available_intents)}
- Active {input_intent.asset} intents: {sum(1 for i in context.available_intents if i.asset == input_intent.asset and i.is_active)}

Use available tools to:
1. Assess inventory position
2. Calculate optimal spread
3. Generate two-sided quote

Provide a competitive quote that balances profit with execution probability."""

        return prompt

    def _format_tool_results(self, tool_results: List[Dict[str, Any]]) -> str:
        """Format tool results"""
        results_str = "Market making analysis:\n"
        for result in tool_results:
            if result["success"]:
                results_str += f"- {result['tool_name']}: {json.dumps(result['result'], indent=2)}\n"
            else:
                results_str += f"- {result['tool_name']}: Error - {result['error']}\n"
        results_str += "\nProvide final liquidity quote in JSON format."
        return results_str


# Testing
if __name__ == "__main__":
    import asyncio
    from services.langgraph import IntentData

    logging.basicConfig(level=logging.INFO)

    async def test_liquidity_agent():
        """Test liquidity agent"""
        print("\n=== Testing Liquidity Agent ===\n")

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
            request_id="liquidity-test-001"
        )

        agent = LiquidityAgent()
        print(f"Agent: {agent.name}")
        print(f"Tools: {len(agent.get_tools())}")

        # Test tools
        print("\n🔧 Testing quote calculation:")
        quote = agent._calculate_quote({
            "asset": "BTC",
            "intent_type": "bid",
            "quantity": 1.0,
            "market_price": 10050.0
        }, context)
        print(f"Bid: ${quote['bid_price']:,.2f}")
        print(f"Ask: ${quote['ask_price']:,.2f}")
        print(f"Spread: {quote['spread_bps']} bps")

        print("\n🔧 Testing inventory assessment:")
        inventory = agent._assess_inventory({"asset": "BTC"}, context)
        print(f"Current position: {inventory['current_position']}")
        print(f"Skew: {inventory['skew_pct']}%")
        print(f"Needs rebalancing: {inventory['needs_rebalancing']}")

        print("\n🔧 Testing spread calculation:")
        spread = agent._calculate_spread({"asset": "BTC", "volatility": 2.5, "inventory_skew": 0.1})
        print(f"Total spread: {spread['spread_pct']}%")
        print(f"Competitive: {spread['competitive']}")

        print("\n✅ Liquidity agent tools working correctly")

    asyncio.run(test_liquidity_agent())
