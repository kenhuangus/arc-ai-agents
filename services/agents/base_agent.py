"""
Base Agent Class for Arc Coordination System

Provides common functionality for all agents:
- LLM integration via router
- Tool definition and execution
- State management
- Logging and observability
- Error handling
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

from services.llm import LLMRouter, ModelPreference

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """
    Context passed to agents containing:
    - Database connections
    - Blockchain state
    - Previous agent results
    - User/system configuration
    """
    # Database session
    db_session: Any = None

    # Blockchain data
    web3: Any = None
    contracts: Dict[str, Any] = field(default_factory=dict)

    # Intent data
    current_intent: Optional[Dict[str, Any]] = None
    available_intents: List[Dict[str, Any]] = field(default_factory=list)

    # Previous agent outputs (for multi-agent workflows)
    previous_results: Dict[str, 'AgentResult'] = field(default_factory=dict)

    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)

    # Request metadata
    request_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentResult:
    """
    Result returned by agents

    Contains:
    - Success/failure status
    - Output data
    - Confidence score
    - Reasoning trace
    - Tool calls made
    - Next agent recommendations
    """
    agent_name: str
    success: bool
    output: Dict[str, Any]
    confidence: float = 0.0  # 0.0 to 1.0
    reasoning: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    next_agent: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "agent_name": self.agent_name,
            "success": self.success,
            "output": self.output,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "tool_calls": self.tool_calls,
            "next_agent": self.next_agent,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class BaseAgent(ABC):
    """
    Abstract base class for all agents

    Subclasses must implement:
    - get_system_prompt(): Return agent-specific system prompt
    - get_tools(): Return list of tool definitions
    - execute_tool(): Handle tool execution
    - run(): Main agent logic

    Features:
    - Automatic LLM routing (Claude/Gemini)
    - Tool use support
    - Conversation history management
    - Error handling and retries
    - Structured output parsing
    """

    def __init__(
        self,
        name: str,
        description: str,
        llm_router: Optional[LLMRouter] = None,
        model_preference: ModelPreference = ModelPreference.AUTO
    ):
        """
        Initialize agent

        Args:
            name: Agent name (e.g., "matching_agent")
            description: Agent description
            llm_router: LLM router instance (creates new if not provided)
            model_preference: Preferred model (AUTO, CLAUDE, GEMINI)
        """
        self.name = name
        self.description = description
        self.llm_router = llm_router or LLMRouter()
        self.model_preference = model_preference

        # Conversation history
        self.messages: List[Dict[str, str]] = []

        # Tool registry
        self._tools: Dict[str, Callable] = {}
        self._register_tools()

        logger.info(f"Initialized {name}: {description}")

    @abstractmethod
    def get_system_prompt(self, context: AgentContext) -> str:
        """
        Get agent-specific system prompt

        Args:
            context: Agent context with data

        Returns:
            System prompt string
        """
        pass

    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions for this agent

        Returns:
            List of tool definitions in Claude format
        """
        pass

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        """
        Main agent execution logic

        Args:
            context: Agent context

        Returns:
            Agent result
        """
        pass

    def _register_tools(self):
        """Register agent tools"""
        tools = self.get_tools()
        for tool in tools:
            tool_name = tool.get("name")
            if tool_name:
                # Store tool definition
                self._tools[tool_name] = tool
        logger.debug(f"Registered {len(self._tools)} tools for {self.name}")

    async def call_llm(
        self,
        prompt: str,
        context: Optional[AgentContext] = None,
        use_tools: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call LLM with automatic routing

        Args:
            prompt: User prompt
            context: Agent context for system prompt
            use_tools: Whether to include tools
            **kwargs: Additional LLM parameters

        Returns:
            LLM response dict
        """
        # Build system prompt
        system_prompt = self.get_system_prompt(context) if context else None

        # Add user message to history
        self.messages.append({"role": "user", "content": prompt})

        # Get tools if requested
        tools = None
        if use_tools and self._tools:
            tools = list(self._tools.values())

        try:
            # Call LLM via router
            response = await self.llm_router.acomplete(
                prompt=prompt,
                system=system_prompt,
                messages=self.messages,
                tools=tools,
                preference=self.model_preference,
                **kwargs
            )

            # Add assistant response to history
            self.messages.append({
                "role": "assistant",
                "content": response["content"]
            })

            logger.info(f"{self.name} LLM call: {response['usage']} tokens via {response['router_model']}")

            return response

        except Exception as e:
            logger.error(f"{self.name} LLM error: {e}")
            raise

    async def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Execute a tool call

        Subclasses should override this to implement tool logic

        Args:
            tool_name: Name of tool to execute
            tool_input: Tool input parameters
            context: Agent context

        Returns:
            Tool execution result
        """
        raise NotImplementedError(
            f"Tool execution not implemented for {self.name}. "
            f"Override execute_tool() to handle '{tool_name}'"
        )

    async def handle_tool_calls(
        self,
        response: Dict[str, Any],
        context: AgentContext
    ) -> List[Dict[str, Any]]:
        """
        Handle tool calls from LLM response

        Args:
            response: LLM response with tool calls
            context: Agent context

        Returns:
            List of tool results
        """
        tool_calls = response.get("tool_calls", [])
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_input = tool_call["input"]

            logger.info(f"{self.name} executing tool: {tool_name}")

            try:
                result = await self.execute_tool(tool_name, tool_input, context)
                results.append({
                    "tool_call_id": tool_call["id"],
                    "tool_name": tool_name,
                    "result": result,
                    "success": True
                })
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                results.append({
                    "tool_call_id": tool_call["id"],
                    "tool_name": tool_name,
                    "error": str(e),
                    "success": False
                })

        return results

    def parse_json_output(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse JSON from LLM response

        Args:
            response: LLM response

        Returns:
            Parsed JSON object
        """
        try:
            # Try using Claude's parser first
            return self.llm_router.claude.parse_json_response(response)
        except Exception as e:
            # Fallback to Gemini parser
            try:
                return self.llm_router.gemini.parse_json_response(response)
            except Exception:
                # Last resort: extract from content
                content = response.get("content", "")
                logger.error(f"Failed to parse JSON from response: {content[:200]}")
                raise e

    def reset_conversation(self):
        """Reset conversation history"""
        self.messages = []
        logger.debug(f"{self.name} conversation reset")

    def get_conversation_summary(self) -> str:
        """Get summary of conversation for logging"""
        return json.dumps(self.messages, indent=2)

    def create_result(
        self,
        success: bool,
        output: Dict[str, Any],
        confidence: float = 0.0,
        reasoning: str = "",
        next_agent: Optional[str] = None,
        error: Optional[str] = None,
        **metadata
    ) -> AgentResult:
        """
        Create AgentResult with standard fields

        Args:
            success: Whether agent succeeded
            output: Agent output data
            confidence: Confidence score (0-1)
            reasoning: Agent reasoning trace
            next_agent: Recommended next agent
            error: Error message if failed
            **metadata: Additional metadata

        Returns:
            AgentResult instance
        """
        return AgentResult(
            agent_name=self.name,
            success=success,
            output=output,
            confidence=confidence,
            reasoning=reasoning,
            next_agent=next_agent,
            error=error,
            metadata=metadata
        )


# Example agent implementation for testing
class ExampleAgent(BaseAgent):
    """Example agent demonstrating base class usage"""

    def __init__(self):
        super().__init__(
            name="example_agent",
            description="Example agent for testing base functionality"
        )

    def get_system_prompt(self, context: AgentContext) -> str:
        return """You are an example agent for the Arc Coordination System.
Your role is to demonstrate how agents work.
Always respond in JSON format with 'message' and 'status' fields."""

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_time",
                "description": "Get current timestamp",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]

    async def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        if tool_name == "get_time":
            return {"timestamp": datetime.now().isoformat()}
        raise ValueError(f"Unknown tool: {tool_name}")

    async def run(self, context: AgentContext) -> AgentResult:
        """Example run method"""
        try:
            response = await self.call_llm(
                prompt="Respond with a test message in JSON format",
                context=context,
                use_tools=False
            )

            output = self.parse_json_output(response)

            return self.create_result(
                success=True,
                output=output,
                confidence=1.0,
                reasoning="Example agent executed successfully"
            )

        except Exception as e:
            return self.create_result(
                success=False,
                output={},
                error=str(e)
            )


# Testing
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def test_agent():
        """Test the example agent"""
        print("\n=== Testing BaseAgent ===\n")

        agent = ExampleAgent()
        context = AgentContext(
            request_id="test-123",
            config={"test": True}
        )

        result = await agent.run(context)

        print(f"Success: {result.success}")
        print(f"Output: {result.output}")
        print(f"Reasoning: {result.reasoning}")

    # Run test
    # asyncio.run(test_agent())
    print("Base agent class created. Test with: python -m services.agents.base_agent")
