"""Claude API wrapper."""

import anthropic


class AIClient:
    """Handles Claude API calls."""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"

    def stream_response(self, prompt: str, max_tokens: int = 2000):
        """Stream a response from Claude."""
        with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                yield text

    def get_response(self, prompt: str, max_tokens: int = 2000) -> str:
        """Get a complete response from Claude."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
