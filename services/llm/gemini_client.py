"""
Gemini 2.5 Pro Client Wrapper

Provides a clean interface for interacting with Google's Gemini models.
Optimized for long-context analysis and document processing.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/.env')

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Wrapper for Gemini 2.5 Pro API

    Features:
    - Long-context processing (up to 2M tokens)
    - Document and code analysis
    - JSON mode for structured outputs
    - Conversation history management
    - Safety settings and content filtering
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-pro",
        temperature: float = 0.7,
        max_output_tokens: int = 8192
    ):
        """
        Initialize Gemini client

        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            model: Model name (default: gemini-2.5-pro)
            temperature: Sampling temperature (0.0-2.0)
            max_output_tokens: Maximum tokens in response
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key or self.api_key == 'your_google_api_key_here':
            logger.warning("No valid Google API key found. Set GOOGLE_API_KEY in config/.env")

        self.model_name = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

        # Configure API
        if self.api_key and self.api_key != 'your_google_api_key_here':
            genai.configure(api_key=self.api_key)

            # Initialize model with safety settings
            generation_config = {
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": max_output_tokens,
            }

            # Lenient safety settings for business use case
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]

            try:
                self.model = genai.GenerativeModel(
                    model_name=model,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                logger.info(f"Gemini client initialized with model: {model}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini model: {e}")
                self.model = None
        else:
            self.model = None
            logger.warning("Gemini model not initialized - no valid API key")

    def complete(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Synchronous completion call

        Args:
            prompt: User prompt
            system_instruction: System instruction/context
            **kwargs: Additional generation parameters

        Returns:
            Response dict with 'content', 'usage', etc.
        """
        if not self.model:
            raise ValueError("Gemini model not initialized. Set GOOGLE_API_KEY in config/.env")

        try:
            # Update model with system instruction if provided
            if system_instruction:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_instruction,
                    generation_config=self.model._generation_config,
                    safety_settings=self.model._safety_settings
                )
            else:
                model = self.model

            # Generate response
            response = model.generate_content(prompt)

            # Parse response
            result = {
                "content": response.text,
                "stop_reason": self._get_finish_reason(response),
                "usage": self._extract_usage(response),
                "model": self.model_name,
                "raw_response": response
            }

            logger.info(f"Gemini completion: {result['usage']['output_tokens']} tokens")
            return result

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    async def acomplete(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Asynchronous completion call

        Args:
            prompt: User prompt
            system_instruction: System instruction
            **kwargs: Additional parameters

        Returns:
            Response dict
        """
        if not self.model:
            raise ValueError("Gemini model not initialized")

        try:
            if system_instruction:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_instruction,
                    generation_config=self.model._generation_config,
                    safety_settings=self.model._safety_settings
                )
            else:
                model = self.model

            response = await model.generate_content_async(prompt)

            result = {
                "content": response.text,
                "stop_reason": self._get_finish_reason(response),
                "usage": self._extract_usage(response),
                "model": self.model_name,
                "raw_response": response
            }

            logger.info(f"Gemini async completion: {result['usage']['output_tokens']} tokens")
            return result

        except Exception as e:
            logger.error(f"Gemini async API error: {e}")
            raise

    def complete_with_history(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete with conversation history

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_instruction: System instruction

        Returns:
            Response dict
        """
        if not self.model:
            raise ValueError("Gemini model not initialized")

        try:
            # Convert messages to Gemini format
            history = []
            for msg in messages[:-1]:  # All except last message
                role = "user" if msg["role"] == "user" else "model"
                history.append({
                    "role": role,
                    "parts": [msg["content"]]
                })

            # Start chat with history
            if system_instruction:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_instruction,
                    generation_config=self.model._generation_config,
                    safety_settings=self.model._safety_settings
                )
            else:
                model = self.model

            chat = model.start_chat(history=history)

            # Send last message
            last_message = messages[-1]["content"]
            response = chat.send_message(last_message)

            result = {
                "content": response.text,
                "stop_reason": self._get_finish_reason(response),
                "usage": self._extract_usage(response),
                "model": self.model_name,
                "raw_response": response
            }

            logger.info(f"Gemini chat completion: {result['usage']['output_tokens']} tokens")
            return result

        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            raise

    def parse_json_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse JSON from Gemini response

        Args:
            response: Response dict from complete()

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

    def _get_finish_reason(self, response) -> str:
        """Extract finish reason from response"""
        try:
            if hasattr(response, 'candidates') and response.candidates:
                return response.candidates[0].finish_reason.name
            return "UNKNOWN"
        except Exception:
            return "UNKNOWN"

    def _extract_usage(self, response) -> Dict[str, int]:
        """Extract token usage from response"""
        try:
            if hasattr(response, 'usage_metadata'):
                metadata = response.usage_metadata
                return {
                    "input_tokens": metadata.prompt_token_count,
                    "output_tokens": metadata.candidates_token_count,
                    "total_tokens": metadata.total_token_count
                }
        except Exception:
            pass

        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text

        Args:
            text: Input text

        Returns:
            Token count
        """
        if not self.model:
            # Rough estimate: ~4 chars per token
            return len(text) // 4

        try:
            result = self.model.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            logger.error(f"Token counting error: {e}")
            return len(text) // 4


# Example usage and testing
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Initialize client
    client = GeminiClient()

    # Test simple completion
    print("\n=== Testing Gemini Client ===\n")

    try:
        response = client.complete(
            prompt="What is the capital of France? Answer in JSON format with 'capital' and 'country' fields.",
            system_instruction="You are a helpful assistant that responds in JSON format."
        )

        print(f"Response: {response['content']}")
        print(f"Tokens used: {response['usage']}")

        # Parse JSON response
        json_data = client.parse_json_response(response)
        print(f"\nParsed JSON: {json_data}")

        # Test token counting
        token_count = client.count_tokens("Hello, world!")
        print(f"\nToken count for 'Hello, world!': {token_count}")

    except Exception as e:
        print(f"Error: {e}")
        print("\nTo test Gemini, set GOOGLE_API_KEY in config/.env")
