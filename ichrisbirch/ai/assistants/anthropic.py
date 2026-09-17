"""Every call the app makes to Claude.

A call runs the Claude Code CLI that `claude-agent-sdk` bundles, authenticated by
the subscription OAuth token in `AI_ANTHROPIC_OAUTH_TOKEN`, so it draws on the
Claude plan rather than API credits. That token authenticates only through Claude
Code, which is why the call is a CLI session and not a Messages API request.

Claude Code ranks `ANTHROPIC_API_KEY` above the OAuth token, so that variable
must never be set in the environment of a process that imports this module.
"""

import dataclasses
import datetime as dt
import enum
import json

import structlog
from claude_agent_sdk import AssistantMessage
from claude_agent_sdk import ClaudeAgentOptions
from claude_agent_sdk import ClaudeSDKError
from claude_agent_sdk import RateLimitEvent
from claude_agent_sdk import RateLimitInfo
from claude_agent_sdk import ResultError
from claude_agent_sdk import ResultMessage
from claude_agent_sdk import query
from pydantic import BaseModel
from pydantic import ValidationError

from ichrisbirch.config import Settings

logger = structlog.get_logger()

# Values Claude Code reports that decide how a failed session is classified.
OUTPUT_TOKEN_CAP_REACHED = 'max_output_tokens'
RATE_LIMITED = 'rate_limit'
STRUCTURED_OUTPUT_RETRIES_EXHAUSTED = 'error_max_structured_output_retries'
LIMIT_REJECTED = 'rejected'

MESSAGE_EXCERPT_CHARS = 160


class AssistantFailure(enum.StrEnum):
    """Why a reply could not be used. Callers branch on this, never on the message."""

    TRUNCATED = 'truncated'
    INVALID_OUTPUT = 'invalid_output'
    FAILED = 'failed'


class AssistantOutputError(Exception):
    """Raised when a call produced no reply that can be used.

    `raw_output` carries what Claude Code actually returned, for whoever has to
    fix the prompt. `str()` stays one short line, because callers record it: the
    bulk import worker writes it to `article_failed_imports.error_message` and
    into a Redis batch payload it rewrites whole on every append.
    """

    def __init__(self, reason: AssistantFailure, message: str, raw_output: str):
        super().__init__(message)
        self.reason = reason
        self.raw_output = raw_output


class AssistantUsageLimitReached(Exception):
    """Raised when the Claude subscription's usage limit refused the call.

    This is not an unusable reply. The same call succeeds once the limit resets,
    so a caller waits for `resets_at` rather than recording a failure. `resets_at`
    is None when Claude Code did not report when the limit lifts.
    """

    def __init__(self, name: str, resets_at: dt.datetime | None, limit_type: str | None):
        when = resets_at.isoformat() if resets_at else 'an unreported time'
        super().__init__(f'{name} reached the Claude {limit_type or "usage"} limit, which resets at {when}')
        self.resets_at = resets_at
        self.limit_type = limit_type


@dataclasses.dataclass
class SessionSignals:
    """What a session reported on the way to its result.

    A failed session's result says only that it failed. These say why.
    """

    limit: RateLimitInfo | None = None
    rate_limited: bool = False
    truncated: bool = False

    def observe(self, message: object) -> None:
        match message:
            case RateLimitEvent():
                self.limit = message.rate_limit_info
            case AssistantMessage(error=error) if error is not None:
                self.rate_limited = self.rate_limited or error == RATE_LIMITED
                self.truncated = self.truncated or error == OUTPUT_TOKEN_CAP_REACHED

    @property
    def usage_limit_reached(self) -> bool:
        """A rate limit that ends a session is the plan's usage limit.

        Claude Code retries a transient 429 before it gives up, so one that reaches
        the result is not going to pass on its own.
        """
        return self.rate_limited or (self.limit is not None and self.limit.status == LIMIT_REJECTED)


class AnthropicAssistant:
    """A one-shot Claude call: a system prompt, the content, and the tools the caller names.

    Each call is a fresh Claude Code session that loads nothing from disk — no
    CLAUDE.md, settings or skills — so the reply depends on the system prompt and
    the content alone. `tools` are the only tools the model has, and they run
    without a permission prompt because nobody is present to answer one.
    """

    def __init__(self, name: str, system_prompt: str, settings: Settings, tools: list[str] | None = None):
        self.name = name
        self.system_prompt = system_prompt
        self.settings = settings
        self.tools = tools or []

    def options(self, max_tokens: int, output_format: dict | None) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            model=self.settings.ai.anthropic.model,
            system_prompt=self.system_prompt,
            tools=self.tools,
            allowed_tools=self.tools,
            setting_sources=[],
            thinking={'type': 'disabled'},
            output_format=output_format,
            env={
                'CLAUDE_CODE_OAUTH_TOKEN': self.settings.ai.anthropic.oauth_token,
                'CLAUDE_CODE_MAX_OUTPUT_TOKENS': str(max_tokens),
            },
            extra_args={'no-session-persistence': None},
        )

    async def generate(self, content: str, max_tokens: int = 4096) -> str:
        """Return the reply as text."""
        result = await self.run(content, max_tokens, output_format=None)
        if result.result is None:
            raise AssistantOutputError(AssistantFailure.INVALID_OUTPUT, f'{self.name} returned no text', '')
        return result.result

    async def generate_structured[Output: BaseModel](self, content: str, output_type: type[Output], max_tokens: int = 4096) -> Output:
        """Return the reply as `output_type`.

        Claude Code holds the reply to the model's JSON Schema. Pydantic validates it
        again, because a model validator — `UrlImportCandidate.payload_matches_kind`
        is one — is a rule a JSON Schema cannot carry.
        """
        output_format = {'type': 'json_schema', 'schema': output_type.model_json_schema()}
        result = await self.run(content, max_tokens, output_format)
        if result.structured_output is None:
            raise AssistantOutputError(AssistantFailure.INVALID_OUTPUT, f'{self.name} returned no structured output', result.result or '')
        try:
            return output_type.model_validate(result.structured_output)
        except ValidationError as e:
            raise AssistantOutputError(
                AssistantFailure.INVALID_OUTPUT,
                f'{self.name} returned output that is not a valid {output_type.__name__} ({e.error_count()} errors)',
                json.dumps(result.structured_output),
            ) from e

    async def run(self, content: str, max_tokens: int, output_format: dict | None) -> ResultMessage:
        """Run one session and return its result, or raise why it produced none."""
        signals = SessionSignals()
        result: ResultMessage | None = None
        try:
            async for message in query(prompt=content, options=self.options(max_tokens, output_format)):
                signals.observe(message)
                if isinstance(message, ResultMessage):
                    result = message
        except ResultError as e:
            raise self.failure(e.subtype, e.api_error_status, e.result or '', signals, max_tokens) from e
        except ClaudeSDKError as e:
            raise AssistantOutputError(
                AssistantFailure.FAILED, f'{self.name} could not run Claude Code ({type(e).__name__})', str(e)
            ) from e

        if result is None:
            raise AssistantOutputError(AssistantFailure.FAILED, f'{self.name} ended without a result', '')
        if result.is_error:
            raise self.failure(result.subtype, result.api_error_status, result.result or '', signals, max_tokens)

        usage = result.usage or {}
        logger.info(
            'anthropic_generated',
            name=self.name,
            input_tokens=usage.get('input_tokens'),
            cache_creation_input_tokens=usage.get('cache_creation_input_tokens'),
            cache_read_input_tokens=usage.get('cache_read_input_tokens'),
            output_tokens=usage.get('output_tokens'),
            turns=result.num_turns,
            duration_ms=result.duration_ms,
            stop_reason=result.stop_reason,
            preview=(result.result or '')[:100],
        )
        return result

    def failure(
        self,
        subtype: str | None,
        api_error_status: int | None,
        text: str,
        signals: SessionSignals,
        max_tokens: int,
    ) -> AssistantOutputError | AssistantUsageLimitReached:
        """Classify a session that ended in an error.

        A capped reply is a fragment that reads as a whole one, so it is refused
        rather than returned — /articles/insights/ would otherwise render half an
        answer with a 200.
        """
        if signals.usage_limit_reached:
            limit = signals.limit
            resets_at = dt.datetime.fromtimestamp(limit.resets_at, dt.UTC) if limit is not None and limit.resets_at else None
            return AssistantUsageLimitReached(self.name, resets_at, limit.rate_limit_type if limit is not None else None)
        if signals.truncated:
            return AssistantOutputError(
                AssistantFailure.TRUNCATED, f'{self.name} reached the {max_tokens} token cap, so its reply is incomplete', text
            )
        if subtype == STRUCTURED_OUTPUT_RETRIES_EXHAUSTED:
            return AssistantOutputError(AssistantFailure.INVALID_OUTPUT, f'{self.name} could not produce output matching its schema', text)
        status = f' (HTTP {api_error_status})' if api_error_status is not None else ''
        excerpt = text.strip().split('\n', 1)[0][:MESSAGE_EXCERPT_CHARS]
        return AssistantOutputError(AssistantFailure.FAILED, f'{self.name} failed{status}: {excerpt}', text)
