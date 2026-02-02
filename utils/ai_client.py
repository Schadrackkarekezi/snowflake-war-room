"""
AI Client - Anthropic API wrapper with streaming support.
"""

import anthropic


class AIClient:
    """Wrapper for Claude API calls with streaming."""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"

    def stream_response(self, prompt: str, max_tokens: int = 2000):
        """
        Stream a response from Claude.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response

        Yields:
            Text chunks as they arrive
        """
        with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                yield text

    def get_response(self, prompt: str, max_tokens: int = 2000) -> str:
        """
        Get a complete response from Claude (non-streaming).

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response

        Returns:
            Complete response text
        """
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
