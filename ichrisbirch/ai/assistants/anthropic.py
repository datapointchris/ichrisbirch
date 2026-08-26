import enum
import json

import structlog
from anthropic import Anthropic

from ichrisbirch.config import Settings

logger = structlog.get_logger()


class AssistantFailure(enum.StrEnum):
    """Why a reply could not be used. Callers branch on this, never on the message."""

    TRUNCATED = 'truncated'
    NOT_JSON = 'not_json'
    NOT_AN_OBJECT = 'not_an_object'


class AssistantOutputError(Exception):
    """Raised when a reply cannot be used.

    `raw_output` carries what the model actually said, for whoever has to fix
    the prompt. `str()` stays one short line, because callers record it: the
    bulk import worker writes it to `article_failed_imports.error_message` and
    into a Redis batch payload it rewrites whole on every append.
    """

    def __init__(self, reason: AssistantFailure, message: str, raw_output: str):
        super().__init__(message)
        self.reason = reason
        self.raw_output = raw_output


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
            stop_reason=response.stop_reason,
            preview=text[:100],
        )
        # A reply stopped at the cap is a fragment that reads as a whole one.
        # A caller that parses it catches the truncation by accident; one that
        # renders it — /articles/insights/ hands this straight to markdown —
        # returns half an answer with a 200 and nothing in the log to say so.
        if response.stop_reason == 'max_tokens':
            raise AssistantOutputError(
                AssistantFailure.TRUNCATED,
                f'{self.name} reached the {max_tokens} token cap, so its reply is incomplete',
                text,
            )
        return text

    @staticmethod
    def _extract_text(response) -> str:
        """Collect all text content blocks in order, skipping tool_use blocks."""
        parts = [block.text for block in response.content if getattr(block, 'type', None) == 'text']
        return ''.join(parts)

    @classmethod
    def parse_json_object(cls, text: str, name: str) -> dict:
        """Parse a reply as a JSON object, or raise with the raw text attached.

        The Messages API returns whatever the model wrote, so a caller reaching
        `.get` on the result is one prose reply away from an AttributeError.
        """
        try:
            parsed = cls.parse_json(text)
        except Exception as e:
            raise AssistantOutputError(AssistantFailure.NOT_JSON, f'{name} returned non-JSON output: {e}', text) from e
        if not isinstance(parsed, dict):
            raise AssistantOutputError(AssistantFailure.NOT_AN_OBJECT, f'{name} returned a non-object top-level value', text)
        return parsed

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
