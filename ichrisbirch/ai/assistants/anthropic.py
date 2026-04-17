import json

import structlog
from anthropic import Anthropic

from ichrisbirch.config import Settings

logger = structlog.get_logger()


class AnthropicAssistant:
    """Stateless wrapper around `client.messages.create`.

    Unlike OpenAI's Assistants API (threads/runs/polling), Anthropic's Messages API is a
    single request/response. One call takes a system prompt, user content, and optional
    tools; it returns the assistant's final text (after any tool-use loops resolve).
    """

    def __init__(self, name: str, system_prompt: str, settings: Settings, tools: list[dict] | None = None):
        self.name = name
        self.system_prompt = system_prompt
        self.settings = settings
        self.tools = tools
        self.client = Anthropic(api_key=self.settings.ai.anthropic.api_key)

    def generate(self, content: str, max_tokens: int = 4096) -> str:
        kwargs: dict = {
            'model': self.settings.ai.anthropic.model,
            'max_tokens': max_tokens,
            'system': self.system_prompt,
            'messages': [{'role': 'user', 'content': content}],
        }
        if self.tools:
            kwargs['tools'] = self.tools

        response = self.client.messages.create(**kwargs)
        text = self._extract_text(response)
        logger.info(
            'anthropic_generated',
            name=self.name,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            preview=text[:100],
        )
        return text

    @staticmethod
    def _extract_text(response) -> str:
        """Collect all text content blocks in order, skipping tool_use blocks."""
        parts = [block.text for block in response.content if getattr(block, 'type', None) == 'text']
        return ''.join(parts)

    @staticmethod
    def parse_json(text: str) -> dict | list:
        """Parse JSON from assistant output, tolerating a code fence wrapper."""
        stripped = text.strip()
        if stripped.startswith('```'):
            # strip leading ```json\n or ```\n and trailing ```
            first_newline = stripped.find('\n')
            if first_newline != -1:
                stripped = stripped[first_newline + 1 :]
            stripped = stripped.removesuffix('```')
            stripped = stripped.strip()
        return json.loads(stripped)
