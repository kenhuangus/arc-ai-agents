"""
LLM Router for Multi-Model Orchestration

Intelligently routes requests to Claude or Gemini based on:
- Task type (tool use, long-context, structured output)
- Cost optimization
- Performance requirements
- Fallback handling
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

from .claude_client import ClaudeClient
from .gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class ModelPreference(Enum):
    """Model preference hints for routing"""
    CLAUDE = "claude"  # Prefer Claude Sonnet 4.5
    GEMINI = "gemini"  # Prefer Gemini 2.5 Pro
    AUTO = "auto"      # Auto-select based on task


class LLMRouter:
    """
    Intelligent router for multi-LLM system

    Routing Logic:
    - Tool use / function calling → Claude (superior tool use)
    - Long context (>100K tokens) → Gemini (2M context window)
    - Structured JSON output → Claude (better at JSON)
    - Market analysis → Gemini (long-context documents)
    - Default → Claude (better general performance)

    Cost Optimization:
    - Claude: $3/MTok input, $15/MTok output
    - Gemini: $1.25/MTok input, $5/MTok output
    - Route high-volume, low-complexity to Gemini
    """

    def __init__(self):
        """Initialize both LLM clients"""
        self.claude = ClaudeClient()
        self.gemini = GeminiClient()

        logger.info("LLM Router initialized with Claude and Gemini")

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        preference: ModelPreference = ModelPreference.AUTO,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Route completion to appropriate model

        Args:
            prompt: User prompt (used if messages not provided)
            system: System instruction
            messages: Conversation history (Claude format)
            tools: Tool definitions (triggers Claude)
            preference: Model preference hint
            **kwargs: Additional parameters

        Returns:
            Response dict with 'content', 'model', 'usage'
        """
        # Select model based on routing logic
        model_choice = self._select_model(
            prompt=prompt,
            messages=messages,
            tools=tools,
            preference=preference,
            **kwargs
        )

        logger.info(f"Routing request to: {model_choice}")

        try:
            if model_choice == "claude":
                return self._complete_claude(prompt, system, messages, tools, **kwargs)
            else:
                return self._complete_gemini(prompt, system, messages, **kwargs)

        except Exception as e:
            logger.error(f"Primary model failed: {e}")

            # Fallback to other model
            if model_choice == "claude":
                logger.info("Falling back to Gemini")
                return self._complete_gemini(prompt, system, messages, **kwargs)
            else:
                logger.info("Falling back to Claude")
                return self._complete_claude(prompt, system, messages, tools, **kwargs)

    def _select_model(
        self,
        prompt: str,
        messages: Optional[List[Dict[str, str]]],
        tools: Optional[List[Dict[str, Any]]],
        preference: ModelPreference,
        **kwargs
    ) -> str:
        """
        Select optimal model based on task characteristics

        Returns:
            "claude" or "gemini"
        """
        # Explicit preference
        if preference == ModelPreference.CLAUDE:
            return "claude"
        elif preference == ModelPreference.GEMINI:
            return "gemini"

        # Tool use always goes to Claude (superior tool calling)
        if tools:
            logger.debug("Selecting Claude for tool use")
            return "claude"

        # Estimate context length
        total_text = prompt
        if messages:
            total_text += " ".join([m.get("content", "") for m in messages])

        estimated_tokens = len(total_text) // 4  # Rough estimate

        # Long context → Gemini
        if estimated_tokens > 100_000:
            logger.debug(f"Selecting Gemini for long context ({estimated_tokens} tokens)")
            return "gemini"

        # Check for keywords suggesting document analysis → Gemini
        analysis_keywords = ["analyze", "summarize", "review", "examine", "market data"]
        if any(kw in prompt.lower() for kw in analysis_keywords):
            logger.debug("Selecting Gemini for analysis task")
            return "gemini"

        # Check for keywords suggesting structured output → Claude
        structured_keywords = ["json", "format", "schema", "structured"]
        if any(kw in prompt.lower() for kw in structured_keywords):
            logger.debug("Selecting Claude for structured output")
            return "claude"

        # Default to Claude (better general performance)
        logger.debug("Selecting Claude (default)")
        return "claude"

    def _complete_claude(
        self,
        prompt: str,
        system: Optional[str],
        messages: Optional[List[Dict[str, str]]],
        tools: Optional[List[Dict[str, Any]]],
        **kwargs
    ) -> Dict[str, Any]:
        """Complete using Claude"""
        # Use messages if provided, otherwise create from prompt
        if not messages:
            messages = [{"role": "user", "content": prompt}]

        response = self.claude.complete(
            messages=messages,
            system=system,
            tools=tools,
            **kwargs
        )

        # Add router metadata
        response["router_model"] = "claude"
        return response

    def _complete_gemini(
        self,
        prompt: str,
        system: Optional[str],
        messages: Optional[List[Dict[str, str]]],
        **kwargs
    ) -> Dict[str, Any]:
        """Complete using Gemini"""
        # Use chat mode if messages provided
        if messages:
            response = self.gemini.complete_with_history(
                messages=messages,
                system_instruction=system
            )
        else:
            response = self.gemini.complete(
                prompt=prompt,
                system_instruction=system,
                **kwargs
            )

        # Add router metadata
        response["router_model"] = "gemini"
        return response

    async def acomplete(
        self,
        prompt: str,
        system: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        preference: ModelPreference = ModelPreference.AUTO,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Async version of complete()

        Args:
            Same as complete()

        Returns:
            Response dict
        """
        model_choice = self._select_model(
            prompt=prompt,
            messages=messages,
            tools=tools,
            preference=preference,
            **kwargs
        )

        logger.info(f"Routing async request to: {model_choice}")

        try:
            if model_choice == "claude":
                if not messages:
                    messages = [{"role": "user", "content": prompt}]
                response = await self.claude.acomplete(
                    messages=messages,
                    system=system,
                    tools=tools,
                    **kwargs
                )
                response["router_model"] = "claude"
                return response
            else:
                response = await self.gemini.acomplete(
                    prompt=prompt,
                    system_instruction=system,
                    **kwargs
                )
                response["router_model"] = "gemini"
                return response

        except Exception as e:
            logger.error(f"Primary async model failed: {e}")

            # Fallback
            if model_choice == "claude":
                logger.info("Falling back to Gemini")
                response = await self.gemini.acomplete(
                    prompt=prompt,
                    system_instruction=system,
                    **kwargs
                )
                response["router_model"] = "gemini"
                return response
            else:
                logger.info("Falling back to Claude")
                if not messages:
                    messages = [{"role": "user", "content": prompt}]
                response = await self.claude.acomplete(
                    messages=messages,
                    system=system,
                    tools=tools,
                    **kwargs
                )
                response["router_model"] = "claude"
                return response

    def get_cost_estimate(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "claude"
    ) -> float:
        """
        Estimate API cost for a request

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: "claude" or "gemini"

        Returns:
            Estimated cost in USD
        """
        if model == "claude":
            # Claude Sonnet 4.5: $3/MTok input, $15/MTok output
            input_cost = (input_tokens / 1_000_000) * 3.0
            output_cost = (output_tokens / 1_000_000) * 15.0
        else:
            # Gemini 2.5 Pro: $1.25/MTok input, $5/MTok output
            input_cost = (input_tokens / 1_000_000) * 1.25
            output_cost = (output_tokens / 1_000_000) * 5.0

        return input_cost + output_cost


# Example usage and testing
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Initialize router
    router = LLMRouter()

    print("\n=== Testing LLM Router ===\n")

    # Test 1: Simple prompt (should route to Claude)
    print("Test 1: Simple prompt")
    try:
        response = router.complete(
            prompt="What is 2+2?",
            system="You are a helpful math assistant."
        )
        print(f"Model used: {response['router_model']}")
        print(f"Response: {response['content'][:100]}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 2: Tool use (should route to Claude)
    print("\nTest 2: Tool use")
    tools = [
        router.claude.create_tool_definition(
            name="get_price",
            description="Get current price of an asset",
            parameters={
                "properties": {
                    "asset": {"type": "string", "description": "Asset symbol"}
                },
                "required": ["asset"]
            }
        )
    ]
    try:
        response = router.complete(
            prompt="What is the price of BTC?",
            tools=tools
        )
        print(f"Model used: {response['router_model']}")
        print(f"Stop reason: {response['stop_reason']}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 3: Cost estimation
    print("\nTest 3: Cost estimation")
    claude_cost = router.get_cost_estimate(10000, 2000, "claude")
    gemini_cost = router.get_cost_estimate(10000, 2000, "gemini")
    print(f"Claude cost (10K input, 2K output): ${claude_cost:.4f}")
    print(f"Gemini cost (10K input, 2K output): ${gemini_cost:.4f}")
    print(f"Gemini savings: {((claude_cost - gemini_cost) / claude_cost * 100):.1f}%")
