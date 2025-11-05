"""
LangGraph Coordination Graph

Defines the multi-agent workflow graph for Arc Coordination System.

Workflow:
  START
    ↓
  matching_agent
    ↓
  ├─ if matches found:
  │   ├─ market_agent (parallel)
  │   └─ fraud_agent (parallel)
  │       ↓
  │       risk_agent
  │           ↓
  │           ├─ if approved: settlement_agent → END
  │           └─ if rejected: END
  │
  └─ if no matches:
      ↓
      liquidity_agent → END
"""

import logging
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END

from .state import CoordinationState, create_initial_state, state_to_dict
from services.agents import (
    MatchingAgent, MarketAgent, RiskAgent,
    FraudAgent, SettlementAgent, LiquidityAgent,
    AgentContext, AgentResult
)

logger = logging.getLogger(__name__)


class CoordinationGraph:
    """
    LangGraph-based multi-agent coordination workflow

    Features:
    - Conditional routing based on agent outputs
    - Parallel agent execution (market + fraud)
    - State persistence across agents
    - Error handling and fallback
    """

    def __init__(self):
        """Initialize coordination graph"""
        # Initialize agents
        self.matching_agent = MatchingAgent()
        self.market_agent = MarketAgent()
        self.risk_agent = RiskAgent()
        self.fraud_agent = FraudAgent()
        self.settlement_agent = SettlementAgent()
        self.liquidity_agent = LiquidityAgent()

        # Build graph
        self.graph = None
        self.compiled_graph = None

        logger.info("Coordination graph initialized with 6 agents")

    def build_graph(self):
        """
        Build the LangGraph workflow

        Graph structure:
        1. matching_agent (entry point)
        2. Conditional: matches found?
           - Yes: market_agent → risk_agent → settlement_agent
           - No: liquidity_agent
        3. END
        """
        workflow = StateGraph(CoordinationState)

        # Add agent nodes
        workflow.add_node("matching_agent", self._matching_node)
        workflow.add_node("market_agent", self._market_node)
        workflow.add_node("fraud_agent", self._fraud_node)
        workflow.add_node("risk_agent", self._risk_node)
        workflow.add_node("settlement_agent", self._settlement_node)
        workflow.add_node("liquidity_agent", self._liquidity_node)

        # Set entry point
        workflow.set_entry_point("matching_agent")

        # Add conditional routing from matching agent
        workflow.add_conditional_edges(
            "matching_agent",
            self._route_after_matching,
            {
                "market_and_fraud": "market_agent",  # Found matches, analyze
                "liquidity": "liquidity_agent",       # No matches, provide liquidity
                "end": END                             # Error or empty
            }
        )

        # Market agent always goes to fraud agent (parallel concept via sequential)
        workflow.add_edge("market_agent", "fraud_agent")

        # Fraud agent goes to risk agent
        workflow.add_edge("fraud_agent", "risk_agent")

        # Add conditional routing from risk agent
        workflow.add_conditional_edges(
            "risk_agent",
            self._route_after_risk,
            {
                "settlement": "settlement_agent",  # Approved, proceed
                "end": END                          # Rejected
            }
        )

        # Settlement and liquidity agents end workflow
        workflow.add_edge("settlement_agent", END)
        workflow.add_edge("liquidity_agent", END)

        # Compile graph (no checkpointer for now, can add later)
        self.compiled_graph = workflow.compile()

        logger.info("Graph compiled successfully")
        return self.compiled_graph

    # Node Functions (wrap agent calls)

    async def _matching_node(self, state: CoordinationState) -> Dict[str, Any]:
        """Execute matching agent"""
        logger.info("→ Executing matching_agent")

        context = self._build_context(state)
        result = await self.matching_agent.run(context)

        # Update state
        state["messages"].append(f"Matching: {result.reasoning}")

        if result.success and result.output.get("matches"):
            # Add matches to state
            from services.langgraph.state import MatchResult
            matches = result.output["matches"]
            for match_dict in matches:
                match_obj = MatchResult(
                    match_id=match_dict["match_id"],
                    intent_a_id=match_dict["intent_a_id"],
                    intent_b_id=match_dict["intent_b_id"],
                    match_score=match_dict["match_score"],
                    confidence=match_dict["confidence"],
                    spread=match_dict["spread"],
                    settlement_price=match_dict["settlement_price"],
                    settlement_quantity=match_dict["settlement_quantity"],
                    reasoning=match_dict["reasoning"]
                )
                state["matches"].append(match_obj)

        # Store result for next agents
        state["metadata"]["matching_result"] = result.to_dict()

        return state

    async def _market_node(self, state: CoordinationState) -> Dict[str, Any]:
        """Execute market agent"""
        logger.info("→ Executing market_agent")

        context = self._build_context(state)
        context.previous_results["matching_agent"] = self._get_agent_result("matching_result", state)

        result = await self.market_agent.run(context)

        state["messages"].append(f"Market: {result.reasoning}")

        if result.success and result.output.get("market_data"):
            from services.langgraph.state import MarketData
            md = result.output["market_data"]
            state["market_data"] = MarketData(
                asset=md["asset"],
                current_price=md["current_price"],
                bid_ask_spread=md["bid_ask_spread"],
                volume_24h=md["volume_24h"],
                volatility=md["volatility"],
                market_sentiment=md["market_sentiment"],
                confidence=md["confidence"]
            )

        state["metadata"]["market_result"] = result.to_dict()

        return state

    async def _fraud_node(self, state: CoordinationState) -> Dict[str, Any]:
        """Execute fraud agent"""
        logger.info("→ Executing fraud_agent")

        context = self._build_context(state)
        context.previous_results["matching_agent"] = self._get_agent_result("matching_result", state)
        context.previous_results["market_agent"] = self._get_agent_result("market_result", state)

        result = await self.fraud_agent.run(context)

        state["messages"].append(f"Fraud: {result.reasoning}")

        if result.success:
            state["fraud_check"] = result.output.get("fraud_check", {})

        state["metadata"]["fraud_result"] = result.to_dict()

        return state

    async def _risk_node(self, state: CoordinationState) -> Dict[str, Any]:
        """Execute risk agent"""
        logger.info("→ Executing risk_agent")

        context = self._build_context(state)
        context.previous_results["matching_agent"] = self._get_agent_result("matching_result", state)
        context.previous_results["market_agent"] = self._get_agent_result("market_result", state)
        context.previous_results["fraud_agent"] = self._get_agent_result("fraud_result", state)

        result = await self.risk_agent.run(context)

        state["messages"].append(f"Risk: {result.reasoning}")

        if result.success:
            state["risk_assessment"] = result.output.get("risk_assessment", {})

        state["metadata"]["risk_result"] = result.to_dict()

        return state

    async def _settlement_node(self, state: CoordinationState) -> Dict[str, Any]:
        """Execute settlement agent"""
        logger.info("→ Executing settlement_agent")

        context = self._build_context(state)
        context.previous_results["matching_agent"] = self._get_agent_result("matching_result", state)
        context.previous_results["risk_agent"] = self._get_agent_result("risk_result", state)

        result = await self.settlement_agent.run(context)

        state["messages"].append(f"Settlement: {result.reasoning}")

        if result.success:
            state["settlement_plan"] = result.output.get("settlement_plan")

        state["metadata"]["settlement_result"] = result.to_dict()
        state["workflow_status"] = "completed"

        return state

    async def _liquidity_node(self, state: CoordinationState) -> Dict[str, Any]:
        """Execute liquidity agent"""
        logger.info("→ Executing liquidity_agent")

        context = self._build_context(state)
        context.previous_results["market_agent"] = self._get_agent_result("market_result", state)

        result = await self.liquidity_agent.run(context)

        state["messages"].append(f"Liquidity: {result.reasoning}")

        if result.success:
            state["metadata"]["liquidity_quote"] = result.output.get("liquidity_quote", {})

        state["metadata"]["liquidity_result"] = result.to_dict()
        state["workflow_status"] = "completed"

        return state

    # Routing Functions

    def _route_after_matching(self, state: CoordinationState) -> str:
        """Route after matching agent"""
        if not state.get("matches") or len(state["matches"]) == 0:
            logger.info("No matches found → liquidity_agent")
            return "liquidity"

        logger.info(f"Found {len(state['matches'])} matches → market_agent")
        return "market_and_fraud"

    def _route_after_risk(self, state: CoordinationState) -> str:
        """Route after risk agent"""
        risk_result = state["metadata"].get("risk_result", {})
        decision = risk_result.get("output", {}).get("decision", "reject")

        if decision == "approve":
            logger.info("Risk approved → settlement_agent")
            return "settlement"
        else:
            logger.info(f"Risk {decision} → END")
            return "end"

    # Helper Functions

    def _build_context(self, state: CoordinationState) -> AgentContext:
        """Build AgentContext from state"""
        return AgentContext(
            current_intent=state["input_intent"],
            available_intents=state["available_intents"],
            request_id=state["request_id"]
        )

    def _get_agent_result(self, result_key: str, state: CoordinationState) -> AgentResult:
        """Convert stored result dict back to AgentResult"""
        result_dict = state["metadata"].get(result_key, {})

        if not result_dict:
            return None

        # Create AgentResult from dict
        from services.agents import AgentResult
        return AgentResult(
            agent_name=result_dict.get("agent_name", "unknown"),
            success=result_dict.get("success", False),
            output=result_dict.get("output", {}),
            confidence=result_dict.get("confidence", 0.0),
            reasoning=result_dict.get("reasoning", ""),
            tool_calls=result_dict.get("tool_calls", []),
            next_agent=result_dict.get("next_agent"),
            error=result_dict.get("error"),
            metadata=result_dict.get("metadata", {})
        )

    async def run(self, initial_state: CoordinationState) -> Dict[str, Any]:
        """
        Execute the coordination workflow

        Args:
            initial_state: Initial workflow state

        Returns:
            Final state after workflow completion
        """
        if not self.compiled_graph:
            self.build_graph()

        logger.info(f"Starting coordination workflow: {initial_state['request_id']}")

        try:
            # Execute graph
            final_state = await self.compiled_graph.ainvoke(initial_state)

            # Convert to dict for JSON serialization
            result = state_to_dict(final_state)

            logger.info(f"Workflow completed: {final_state['workflow_status']}")

            return {
                "success": True,
                "request_id": final_state["request_id"],
                "workflow_status": final_state["workflow_status"],
                "matches": [m.to_dict() for m in final_state.get("matches", [])],
                "market_data": final_state["market_data"].to_dict() if final_state.get("market_data") else None,
                "risk_assessment": final_state.get("risk_assessment", {}),
                "fraud_check": final_state.get("fraud_check", {}),
                "settlement_plan": final_state.get("settlement_plan"),
                "messages": final_state["messages"],
                "metadata": final_state["metadata"]
            }

        except Exception as e:
            logger.error(f"Workflow error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "request_id": initial_state["request_id"]
            }


# Testing
if __name__ == "__main__":
    import asyncio
    from services.langgraph import IntentData
    from datetime import datetime

    logging.basicConfig(level=logging.INFO)

    async def test_graph():
        """Test coordination graph"""
        print("\n=== Testing Coordination Graph ===\n")

        # Create test intents
        bid_intent = IntentData(
            intent_id="0xBID001",
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
            intent_id="0xASK001",
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

        # Create initial state
        initial_state = create_initial_state(
            input_intent=bid_intent,
            available_intents=[ask_intent],
            request_id="test-graph-001"
        )

        # Build and run graph
        graph = CoordinationGraph()
        graph.build_graph()

        print("Graph built successfully")
        print(f"Nodes: matching, market, fraud, risk, settlement, liquidity")
        print(f"\nStarting workflow for: {bid_intent.intent_id}")

        result = await graph.run(initial_state)

        print(f"\n✅ Workflow completed!")
        print(f"Status: {result['workflow_status']}")
        print(f"Matches: {len(result.get('matches', []))}")
        print(f"Messages: {len(result['messages'])}")

    asyncio.run(test_graph())
