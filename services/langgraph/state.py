"""
LangGraph State Schema for Arc Coordination System

Defines the state structure for multi-agent workflows:
- Intent data
- Match results
- Market analysis
- Risk assessments
- Agent communication
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from dataclasses import dataclass, field
from datetime import datetime
import operator


# Type definitions for state channels
def merge_lists(left: List, right: List) -> List:
    """Merge two lists by appending"""
    return left + right


def merge_dicts(left: Dict, right: Dict) -> Dict:
    """Merge two dicts by updating"""
    result = left.copy()
    result.update(right)
    return result


@dataclass
class IntentData:
    """
    Intent information passed through the workflow
    """
    intent_id: str
    intent_hash: str
    actor: str
    intent_type: str  # "bid" or "ask"
    price: float
    quantity: float
    asset: str
    settlement_asset: str
    timestamp: int
    valid_until: int
    ap2_mandate_id: str
    is_active: bool
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_db(cls, intent_db: Any) -> 'IntentData':
        """Create from database record"""
        import json
        payload = json.loads(intent_db.payload) if isinstance(intent_db.payload, str) else intent_db.payload

        return cls(
            intent_id=intent_db.intent_id,
            intent_hash=intent_db.intent_hash,
            actor=intent_db.actor,
            intent_type=payload.get("type", "bid"),
            price=payload.get("price", 0),
            quantity=payload.get("quantity", 0),
            asset=payload.get("asset", "BTC"),
            settlement_asset=intent_db.settlement_asset,
            timestamp=intent_db.timestamp,
            valid_until=intent_db.valid_until,
            ap2_mandate_id=intent_db.ap2_mandate_id,
            is_active=intent_db.is_active,
            payload=payload,
            metadata={}
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "intent_id": self.intent_id,
            "intent_hash": self.intent_hash,
            "actor": self.actor,
            "intent_type": self.intent_type,
            "price": self.price,
            "quantity": self.quantity,
            "asset": self.asset,
            "settlement_asset": self.settlement_asset,
            "timestamp": self.timestamp,
            "valid_until": self.valid_until,
            "ap2_mandate_id": self.ap2_mandate_id,
            "is_active": self.is_active,
            "payload": self.payload,
            "metadata": self.metadata
        }


@dataclass
class MatchResult:
    """
    Result from matching agent
    """
    match_id: str
    intent_a_id: str
    intent_b_id: str
    match_score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    spread: float  # Price difference
    settlement_price: float
    settlement_quantity: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "match_id": self.match_id,
            "intent_a_id": self.intent_a_id,
            "intent_b_id": self.intent_b_id,
            "match_score": self.match_score,
            "confidence": self.confidence,
            "spread": self.spread,
            "settlement_price": self.settlement_price,
            "settlement_quantity": self.settlement_quantity,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class MarketData:
    """
    Market analysis data
    """
    asset: str
    current_price: float
    bid_ask_spread: float
    volume_24h: float
    volatility: float
    market_sentiment: str  # "bullish", "bearish", "neutral"
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "asset": self.asset,
            "current_price": self.current_price,
            "bid_ask_spread": self.bid_ask_spread,
            "volume_24h": self.volume_24h,
            "volatility": self.volatility,
            "market_sentiment": self.market_sentiment,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class CoordinationState(TypedDict):
    """
    Main state schema for Arc Coordination multi-agent workflow

    This state is passed through all agents and updated incrementally.
    Uses typed channels for type safety and state reducers for merging.

    Channels:
    - input_intent: The intent being processed
    - available_intents: Pool of candidate intents for matching
    - matches: Potential matches found by matching agent
    - market_data: Market analysis from market agent
    - risk_assessment: Risk analysis from risk agent
    - fraud_check: Fraud detection results
    - settlement_plan: Settlement coordination data
    - messages: Agent communication log
    - errors: Error tracking
    - metadata: Additional context
    """

    # Primary intent being coordinated
    input_intent: IntentData

    # Pool of available intents for matching
    available_intents: List[IntentData]

    # Potential matches found
    matches: Annotated[List[MatchResult], merge_lists]

    # Market analysis
    market_data: Optional[MarketData]

    # Risk assessment results
    risk_assessment: Dict[str, Any]

    # Fraud detection results
    fraud_check: Dict[str, Any]

    # Settlement coordination
    settlement_plan: Optional[Dict[str, Any]]

    # Agent messages and reasoning
    messages: Annotated[List[str], merge_lists]

    # Error tracking
    errors: Annotated[List[str], merge_lists]

    # Next agent to route to
    next_agent: Optional[str]

    # Workflow control
    workflow_status: str  # "running", "completed", "failed"

    # Request metadata
    request_id: str
    timestamp: datetime

    # Flexible metadata
    metadata: Annotated[Dict[str, Any], merge_dicts]


def create_initial_state(
    input_intent: IntentData,
    available_intents: List[IntentData],
    request_id: str = ""
) -> CoordinationState:
    """
    Create initial state for workflow

    Args:
        input_intent: Intent to coordinate
        available_intents: Pool of available intents
        request_id: Request identifier

    Returns:
        Initial coordination state
    """
    return CoordinationState(
        input_intent=input_intent,
        available_intents=available_intents,
        matches=[],
        market_data=None,
        risk_assessment={},
        fraud_check={},
        settlement_plan=None,
        messages=[],
        errors=[],
        next_agent=None,
        workflow_status="running",
        request_id=request_id,
        timestamp=datetime.now(),
        metadata={}
    )


def state_to_dict(state: CoordinationState) -> Dict[str, Any]:
    """
    Convert state to dictionary for JSON serialization

    Args:
        state: Coordination state

    Returns:
        Dictionary representation
    """
    return {
        "input_intent": state["input_intent"].to_dict() if state.get("input_intent") else None,
        "available_intents": [intent.to_dict() for intent in state.get("available_intents", [])],
        "matches": [match.to_dict() for match in state.get("matches", [])],
        "market_data": state["market_data"].to_dict() if state.get("market_data") else None,
        "risk_assessment": state.get("risk_assessment", {}),
        "fraud_check": state.get("fraud_check", {}),
        "settlement_plan": state.get("settlement_plan"),
        "messages": state.get("messages", []),
        "errors": state.get("errors", []),
        "next_agent": state.get("next_agent"),
        "workflow_status": state.get("workflow_status", "unknown"),
        "request_id": state.get("request_id", ""),
        "timestamp": state["timestamp"].isoformat() if state.get("timestamp") else None,
        "metadata": state.get("metadata", {})
    }


# Example usage
if __name__ == "__main__":
    print("=== LangGraph State Schema ===\n")

    # Create example intent
    test_intent = IntentData(
        intent_id="0x123",
        intent_hash="0xabc",
        actor="0xUser1",
        intent_type="bid",
        price=10000.0,
        quantity=1.0,
        asset="BTC",
        settlement_asset="USD",
        timestamp=int(datetime.now().timestamp()),
        valid_until=int(datetime.now().timestamp()) + 86400,
        ap2_mandate_id="0xMandate1",
        is_active=True
    )

    # Create initial state
    state = create_initial_state(
        input_intent=test_intent,
        available_intents=[],
        request_id="test-001"
    )

    print(f"State created: {state['request_id']}")
    print(f"Input intent: {state['input_intent'].intent_id}")
    print(f"Workflow status: {state['workflow_status']}")

    # Add a message
    state["messages"].append("Test message from matching agent")
    print(f"\nMessages: {state['messages']}")

    print("\n✅ State schema working correctly")
