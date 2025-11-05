"""
Market Agent for Arc Coordination System

Analyzes market conditions and provides price intelligence for intent matching.

Capabilities:
- Analyze current market prices and trends
- Calculate bid-ask spreads
- Assess market volatility
- Provide fair value estimates
- Detect market manipulation or anomalies
"""

import logging
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random

from .base_agent import BaseAgent, AgentContext, AgentResult
from services.llm import ModelPreference
from services.langgraph.state import MarketData

logger = logging.getLogger(__name__)


class MarketAgent(BaseAgent):
    """
    Market analysis agent

    Uses Gemini 2.5 Pro for:
    - Long-context market data analysis
    - Historical trend analysis
    - Multi-asset correlation
    - Market sentiment assessment

    Analysis Criteria:
    1. Current market price vs intent prices
    2. Historical volatility (24h, 7d, 30d)
    3. Bid-ask spread health
    4. Volume and liquidity
    5. Market sentiment (bullish/bearish/neutral)
    """

    def __init__(self):
        super().__init__(
            name="market_agent",
            description="Analyzes market conditions and provides price intelligence",
            model_preference=ModelPreference.GEMINI  # Gemini for long-context analysis
        )

    def get_system_prompt(self, context: AgentContext) -> str:
        """Get system prompt for market agent"""
        return """You are an expert market analysis agent for the Arc Coordination System.

Your role is to analyze market conditions for intent matching and settlement.

ANALYSIS FRAMEWORK:
1. Price Analysis: Compare intent prices with market prices
2. Volatility: Assess price stability and risk
3. Liquidity: Check market depth and trading volume
4. Sentiment: Determine market direction (bullish/bearish/neutral)
5. Fairness: Validate that settlement prices are fair

MARKET CONDITIONS:
- Tight spread (<1%): Healthy market, high confidence
- Medium spread (1-3%): Normal market conditions
- Wide spread (>3%): Low liquidity, lower confidence
- High volatility (>5% daily): Risky conditions
- Low volume: Liquidity concerns

SENTIMENT SCORING:
- Bullish: Buying pressure, prices rising, positive momentum
- Bearish: Selling pressure, prices falling, negative momentum
- Neutral: Balanced market, sideways movement

You must respond in valid JSON format with this exact structure:
{
  "market_data": {
    "asset": "BTC",
    "current_price": 10050.0,
    "bid_ask_spread": 0.5,
    "volume_24h": 1234.5,
    "volatility": 2.3,
    "market_sentiment": "neutral",
    "confidence": 0.85
  },
  "analysis": {
    "price_assessment": "Intent prices are within market range",
    "liquidity_assessment": "Adequate liquidity for settlement",
    "risk_level": "low",
    "recommendation": "proceed"
  },
  "reasoning": "Market conditions are stable with low volatility..."
}

IMPORTANT: Always return valid JSON. No markdown, no code blocks, just pure JSON."""

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get tool definitions for market agent"""
        return [
            {
                "name": "get_market_price",
                "description": "Fetch current market price for an asset",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "asset": {"type": "string", "description": "Asset symbol (BTC, ETH, etc.)"},
                        "source": {"type": "string", "description": "Price source (optional)"}
                    },
                    "required": ["asset"]
                }
            },
            {
                "name": "calculate_volatility",
                "description": "Calculate historical volatility for an asset",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "asset": {"type": "string", "description": "Asset symbol"},
                        "period": {"type": "string", "description": "Time period: 24h, 7d, 30d"}
                    },
                    "required": ["asset", "period"]
                }
            },
            {
                "name": "get_market_depth",
                "description": "Get order book depth and liquidity metrics",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "asset": {"type": "string", "description": "Asset symbol"}
                    },
                    "required": ["asset"]
                }
            }
        ]

    async def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Execute market-specific tools"""
        if tool_name == "get_market_price":
            return await self._get_market_price(tool_input, context)

        elif tool_name == "calculate_volatility":
            return self._calculate_volatility(tool_input, context)

        elif tool_name == "get_market_depth":
            return self._get_market_depth(tool_input, context)

        raise ValueError(f"Unknown tool: {tool_name}")

    async def _get_market_price(
        self,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Fetch current market price

        In production, this would call:
        - CoinGecko API
        - Binance API
        - Chainlink price feeds
        - Internal price oracle

        For now, derives from intent prices in database
        """
        asset = tool_input["asset"]

        # Get prices from available intents
        prices = []
        for intent in context.available_intents:
            if intent.asset == asset and intent.is_active:
                prices.append(intent.price)

        if not prices:
            # Fallback to mock data
            mock_prices = {
                "BTC": 10050.0,
                "ETH": 1800.0,
                "USDC": 1.0,
                "USD": 1.0
            }
            return {
                "asset": asset,
                "price": mock_prices.get(asset, 0),
                "source": "mock",
                "timestamp": int(datetime.now().timestamp())
            }

        # Calculate average from active intents
        avg_price = sum(prices) / len(prices)

        return {
            "asset": asset,
            "price": round(avg_price, 2),
            "source": "intent_pool",
            "sample_size": len(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "timestamp": int(datetime.now().timestamp())
        }

    def _calculate_volatility(
        self,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Calculate historical volatility

        In production, this would analyze:
        - Historical price data
        - Standard deviation
        - Average true range (ATR)
        - Bollinger band width

        For now, returns mock volatility based on asset
        """
        asset = tool_input["asset"]
        period = tool_input.get("period", "24h")

        # Mock volatility data
        base_volatility = {
            "BTC": 2.5,
            "ETH": 3.5,
            "USDC": 0.1,
            "USD": 0.0
        }

        volatility = base_volatility.get(asset, 5.0)

        # Add some randomness
        volatility += random.uniform(-0.5, 0.5)

        return {
            "asset": asset,
            "period": period,
            "volatility_pct": round(volatility, 2),
            "level": "low" if volatility < 2 else "medium" if volatility < 5 else "high",
            "timestamp": int(datetime.now().timestamp())
        }

    def _get_market_depth(
        self,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Get order book depth

        In production, this would fetch:
        - Order book from exchanges
        - Liquidity depth
        - Slippage estimates

        For now, derives from intent pool
        """
        asset = tool_input["asset"]

        # Count active intents by type
        bids = [i for i in context.available_intents if i.asset == asset and i.intent_type == "bid" and i.is_active]
        asks = [i for i in context.available_intents if i.asset == asset and i.intent_type == "ask" and i.is_active]

        bid_volume = sum([i.quantity for i in bids])
        ask_volume = sum([i.quantity for i in asks])

        # Calculate spread
        if bids and asks:
            best_bid = max([i.price for i in bids])
            best_ask = min([i.price for i in asks])
            spread_pct = ((best_ask - best_bid) / best_ask) * 100
        else:
            best_bid = 0
            best_ask = 0
            spread_pct = 0

        return {
            "asset": asset,
            "bid_count": len(bids),
            "ask_count": len(asks),
            "bid_volume": round(bid_volume, 4),
            "ask_volume": round(ask_volume, 4),
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread_pct": round(spread_pct, 2),
            "liquidity_score": min(1.0, (len(bids) + len(asks)) / 10),
            "timestamp": int(datetime.now().timestamp())
        }

    async def run(self, context: AgentContext) -> AgentResult:
        """
        Execute market analysis

        Args:
            context: Agent context with intent and match data

        Returns:
            AgentResult with market analysis
        """
        try:
            input_intent = context.current_intent
            if not input_intent:
                return self.create_result(
                    success=False,
                    output={},
                    error="No input intent provided"
                )

            logger.info(f"Market agent analyzing {input_intent.asset}")

            # Build analysis prompt
            prompt = self._build_market_prompt(input_intent, context)

            # Call LLM with tools
            response = await self.call_llm(
                prompt=prompt,
                context=context,
                use_tools=True,
                temperature=0.5  # Moderate temperature for analysis
            )

            # Handle tool calls if requested
            if response.get("stop_reason") == "tool_use":
                tool_results = await self.handle_tool_calls(response, context)

                # Continue with tool results
                tool_result_message = self._format_tool_results(tool_results)
                response = await self.call_llm(
                    prompt=tool_result_message,
                    context=context,
                    use_tools=False
                )

            # Parse market analysis
            output = self.parse_json_output(response)

            # Create MarketData object
            market_data_dict = output.get("market_data", {})
            market_data = MarketData(
                asset=market_data_dict.get("asset", input_intent.asset),
                current_price=market_data_dict.get("current_price", 0),
                bid_ask_spread=market_data_dict.get("bid_ask_spread", 0),
                volume_24h=market_data_dict.get("volume_24h", 0),
                volatility=market_data_dict.get("volatility", 0),
                market_sentiment=market_data_dict.get("market_sentiment", "neutral"),
                confidence=market_data_dict.get("confidence", 0.5)
            )

            analysis = output.get("analysis", {})
            reasoning = output.get("reasoning", "")

            # Determine next agent based on risk
            risk_level = analysis.get("risk_level", "medium")
            next_agent = "risk_agent" if risk_level != "critical" else None

            logger.info(f"Market analysis complete: {market_data.market_sentiment} sentiment, {risk_level} risk")

            return self.create_result(
                success=True,
                output={
                    "market_data": market_data.to_dict(),
                    "analysis": analysis,
                    "reasoning": reasoning
                },
                confidence=market_data.confidence,
                reasoning=reasoning,
                next_agent=next_agent
            )

        except Exception as e:
            logger.error(f"Market agent error: {e}", exc_info=True)
            return self.create_result(
                success=False,
                output={},
                error=str(e)
            )

    def _build_market_prompt(
        self,
        input_intent: Any,
        context: AgentContext
    ) -> str:
        """Build prompt for market analysis"""
        # Get previous agent results if available
        previous_matches = context.previous_results.get("matching_agent")

        prompt = f"""Analyze the market conditions for this intent and its matches:

INPUT INTENT:
- Asset: {input_intent.asset}
- Type: {input_intent.intent_type}
- Price: ${input_intent.price:,.2f}
- Quantity: {input_intent.quantity}
- Settlement Asset: {input_intent.settlement_asset}

MARKET CONTEXT:
- Active intents in pool: {len(context.available_intents)}
- Intent pool by asset: {self._count_by_asset(context.available_intents)}
"""

        if previous_matches and previous_matches.output.get("matches"):
            matches = previous_matches.output["matches"]
            prompt += f"\nPOTENTIAL MATCHES: {len(matches)}\n"
            for match in matches[:3]:  # Show top 3 matches
                prompt += f"- Settlement: ${match['settlement_price']:,.2f} x {match['settlement_quantity']}\n"
                prompt += f"  Spread: ${match['spread']:,.2f}\n"

        prompt += """
Use the available tools to gather market data, then provide a comprehensive analysis.
Focus on: price fairness, market liquidity, volatility risk, and settlement feasibility.
"""

        return prompt

    def _count_by_asset(self, intents: List) -> Dict[str, int]:
        """Count intents by asset"""
        counts = {}
        for intent in intents:
            if intent.is_active:
                counts[intent.asset] = counts.get(intent.asset, 0) + 1
        return counts

    def _format_tool_results(self, tool_results: List[Dict[str, Any]]) -> str:
        """Format tool results for continuation"""
        results_str = "Market data gathered:\n"
        for result in tool_results:
            if result["success"]:
                results_str += f"- {result['tool_name']}: {json.dumps(result['result'], indent=2)}\n"
            else:
                results_str += f"- {result['tool_name']}: Error - {result['error']}\n"
        results_str += "\nNow provide the final JSON analysis with your assessment."
        return results_str


# Testing
if __name__ == "__main__":
    import asyncio
    from services.langgraph import IntentData

    logging.basicConfig(level=logging.INFO)

    async def test_market_agent():
        """Test market agent"""
        print("\n=== Testing Market Agent ===\n")

        # Create test intent
        intent = IntentData(
            intent_id="0xTEST",
            intent_hash="0xhash",
            actor="0xUser",
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

        # Create context with some market intents
        available_intents = [
            IntentData(
                intent_id=f"0xINT{i}",
                intent_hash=f"0x{i}",
                actor=f"0xUser{i}",
                intent_type="ask" if i % 2 == 0 else "bid",
                price=10000.0 + (i * 50),
                quantity=0.5,
                asset="BTC",
                settlement_asset="USD",
                timestamp=int(datetime.now().timestamp()),
                valid_until=int(datetime.now().timestamp()) + 86400,
                ap2_mandate_id=f"0xM{i}",
                is_active=True
            )
            for i in range(5)
        ]

        context = AgentContext(
            current_intent=intent,
            available_intents=available_intents,
            request_id="market-test-001"
        )

        # Test agent
        agent = MarketAgent()
        print(f"Agent: {agent.name}")
        print(f"Tools: {len(agent.get_tools())}")

        # Test tools directly
        print("\n🔧 Testing market price tool:")
        price_result = await agent._get_market_price({"asset": "BTC"}, context)
        print(f"Price: ${price_result['price']:,.2f}")
        print(f"Source: {price_result['source']}")

        print("\n🔧 Testing volatility tool:")
        vol_result = agent._calculate_volatility({"asset": "BTC", "period": "24h"}, context)
        print(f"Volatility: {vol_result['volatility_pct']}%")
        print(f"Level: {vol_result['level']}")

        print("\n🔧 Testing market depth tool:")
        depth_result = agent._get_market_depth({"asset": "BTC"}, context)
        print(f"Bids: {depth_result['bid_count']}, Asks: {depth_result['ask_count']}")
        print(f"Spread: {depth_result['spread_pct']}%")
        print(f"Liquidity score: {depth_result['liquidity_score']}")

        print("\n✅ Market agent tools working correctly")

    asyncio.run(test_market_agent())
