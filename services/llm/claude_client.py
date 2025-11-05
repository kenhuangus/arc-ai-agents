"""
Claude Sonnet 4.5 Client Wrapper

Provides a clean interface for interacting with Claude via Anthropic API.
Supports tool use, structured outputs, and streaming.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Union
from anthropic import Anthropic, AsyncAnthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/.env')

logger = logging.getLogger(__name__)


class ClaudeClient:
    """
    Wrapper for Claude Sonnet 4.5 API

    Features:
    - Synchronous and asynchronous calls
    - Tool use support for agent actions
    - Structured JSON outputs
    - Conversation history management
    - Error handling and retries
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929",
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        """
        Initialize Claude client

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model name (default: claude-sonnet-4-5-20250929)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key or self.api_key == 'your_anthropic_api_key_here':
            logger.warning("No valid Anthropic API key found. Set ANTHROPIC_API_KEY in config/.env")

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Initialize clients
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None
        self.async_client = AsyncAnthropic(api_key=self.api_key) if self.api_key else None

        logger.info(f"Claude client initialized with model: {model}")

    def complete(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Synchronous completion call

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: System prompt
            tools: Tool definitions for function calling
            **kwargs: Additional API parameters

        Returns:
            Response dict with 'content', 'stop_reason', 'usage', etc.
        """
        if not self.client:
            raise ValueError("Claude client not initialized. Set ANTHROPIC_API_KEY in config/.env")

        try:
            params = {
                "model": self.model,
                "max_tokens": kwargs.get('max_tokens', self.max_tokens),
                "temperature": kwargs.get('temperature', self.temperature),
                "messages": messages
            }

            if system:
                params['system'] = system

            if tools:
                params['tools'] = tools

            response = self.client.messages.create(**params)

            # Parse response
            result = {
                "content": self._extract_content(response.content),
                "stop_reason": response.stop_reason,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "model": response.model,
                "raw_response": response
            }

            # Extract tool calls if present
            if response.stop_reason == "tool_use":
                result["tool_calls"] = self._extract_tool_calls(response.content)

            logger.info(f"Claude completion: {result['usage']['output_tokens']} tokens")
            return result

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise

    async def acomplete(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Asynchronous completion call

        Args:
            messages: List of message dicts
            system: System prompt
            tools: Tool definitions
            **kwargs: Additional API parameters

        Returns:
            Response dict
        """
        if not self.async_client:
            raise ValueError("Claude async client not initialized")

        try:
            params = {
                "model": self.model,
                "max_tokens": kwargs.get('max_tokens', self.max_tokens),
                "temperature": kwargs.get('temperature', self.temperature),
                "messages": messages
            }

            if system:
                params['system'] = system

            if tools:
                params['tools'] = tools

            response = await self.async_client.messages.create(**params)

            result = {
                "content": self._extract_content(response.content),
                "stop_reason": response.stop_reason,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "model": response.model,
                "raw_response": response
            }

            if response.stop_reason == "tool_use":
                result["tool_calls"] = self._extract_tool_calls(response.content)

            logger.info(f"Claude async completion: {result['usage']['output_tokens']} tokens")
            return result

        except Exception as e:
            logger.error(f"Claude async API error: {e}")
            raise

    def _extract_content(self, content: List[Any]) -> str:
        """Extract text content from response"""
        text_blocks = [block.text for block in content if hasattr(block, 'text')]
        return "\n".join(text_blocks)

    def _extract_tool_calls(self, content: List[Any]) -> List[Dict[str, Any]]:
        """Extract tool use blocks from response"""
        tool_calls = []
        for block in content:
            if hasattr(block, 'type') and block.type == 'tool_use':
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
        return tool_calls

    def parse_json_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse JSON from Claude response

        Args:
            response: Response dict from complete() or acomplete()

        Returns:
            Parsed JSON object
        """
        content = response.get('content', '')

        # Try to extract JSON from markdown code blocks
        if '```json' in content:
            json_str = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            json_str = content.split('```')[1].split('```')[0].strip()
        else:
            json_str = content.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Content: {content}")
            raise

    def create_tool_definition(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a tool definition for Claude

        Args:
            name: Tool name
            description: Tool description
            parameters: JSON schema for parameters

        Returns:
            Tool definition dict
        """
        return {
            "name": name,
            "description": description,
            "input_schema": {
                "type": "object",
                "properties": parameters.get("properties", {}),
                "required": parameters.get("required", [])
            }
        }


# Example usage and testing
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Initialize client
    client = ClaudeClient()

    # Test simple completion
    print("\n=== Testing Claude Client ===\n")

    try:
        response = client.complete(
            messages=[
                {"role": "user", "content": "What is the capital of France? Answer in JSON format with 'capital' and 'country' fields."}
            ],
            system="You are a helpful assistant that responds in JSON format."
        )

        print(f"Response: {response['content']}")
        print(f"Tokens used: {response['usage']}")

        # Parse JSON response
        json_data = client.parse_json_response(response)
        print(f"\nParsed JSON: {json_data}")

    except Exception as e:
        print(f"Error: {e}")
        print("\nTo test Claude, set ANTHROPIC_API_KEY in config/.env")
