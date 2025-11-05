"""
LangGraph State Management for Arc Coordination

Multi-agent workflow orchestration using LangGraph:
- State schema definitions
- Agent graph construction
- Conditional routing
- State persistence
"""

from .state import CoordinationState, IntentData, MatchResult, MarketData

# Import graph lazily to avoid circular imports
# Use: from services.langgraph.graph import CoordinationGraph
def __getattr__(name):
    if name == 'CoordinationGraph':
        from .graph import CoordinationGraph
        return CoordinationGraph
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    'CoordinationState',
    'IntentData',
    'MatchResult',
    'MarketData',
    'CoordinationGraph'
]
