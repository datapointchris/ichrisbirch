"""Tests for AnthropicAssistant.

The stub tests replace `claude_agent_sdk.query` with the messages Claude Code
emits, and check how each outcome is classified. `TestRealClaudeCode` starts the
bundled CLI with a token the API refuses, which proves the CLI accepts every flag
the wrapper passes without drawing anything from the plan.
"""

import datetime as dt
import os
from typing import cast
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from claude_agent_sdk import AssistantMessage
from claude_agent_sdk import CLINotFoundError
from claude_agent_sdk import RateLimitEvent
from claude_agent_sdk import RateLimitInfo
from claude_agent_sdk import RateLimitStatus
from claude_agent_sdk import RateLimitType
from claude_agent_sdk import ResultError
from claude_agent_sdk import ResultMessage
from claude_agent_sdk.types import AssistantMessageError
from pydantic import BaseModel
from pydantic import model_validator

from ichrisbirch.ai.assistants.anthropic import AnthropicAssistant
from ichrisbirch.ai.assistants.anthropic import AssistantFailure
from ichrisbirch.ai.assistants.anthropic import AssistantOutputError
from ichrisbirch.ai.assistants.anthropic import AssistantUsageLimitReached


class Reply(BaseModel):
    summary: str
    tags: list[str]

    @model_validator(mode='after')
    def has_a_tag(self):
        if not self.tags:
            raise ValueError('a reply needs at least one tag')
        return self


def make_assistant(tools: list[str] | None = None, token: str = 'test-token') -> AnthropicAssistant:
    settings = MagicMock()
    settings.ai.anthropic.oauth_token = token
    settings.ai.anthropic.model = 'claude-sonnet-4-6'
    return AnthropicAssistant(name='Test Assistant', system_prompt='be brief', settings=settings, tools=tools)


def result_message(
    result: str | None = 'all of it',
    structured_output: object = None,
    is_error: bool = False,
    api_error_status: int | None = None,
) -> ResultMessage:
    return ResultMessage(
        subtype='success',
        duration_ms=10,
        duration_api_ms=8,
        is_error=is_error,
        num_turns=1,
        session_id='session',
        result=result,
        structured_output=structured_output,
        api_error_status=api_error_status,
        usage={'input_tokens': 10, 'output_tokens': 20},
    )


def result_error(text: str, **data) -> ResultError:
    return ResultError(f'Claude Code returned an error result: {text}', data={'subtype': 'success', 'result': text} | data, exit_code=1)


def rate_limit(status: RateLimitStatus, resets_at: int | None = None, limit_type: RateLimitType | None = 'five_hour') -> RateLimitEvent:
    info = RateLimitInfo(status=status, resets_at=resets_at, rate_limit_type=limit_type)
    return RateLimitEvent(rate_limit_info=info, uuid='event', session_id='session')


def assistant_error(error: str) -> AssistantMessage:
    """An assistant message carrying `error`.

    Claude Code emits `max_output_tokens`, which the SDK's `AssistantMessageError`
    does not list, so the value is cast rather than typed.
    """
    return AssistantMessage(content=[], model='claude-sonnet-4-6', error=cast(AssistantMessageError, error))


def stub_session(*messages, raises: Exception | None = None):
    """Patch `query` to yield `messages`, then raise `raises` if one is given.

    Returns the patch and the list each call's options are appended to.
    """
    calls = []

    async def fake_query(prompt, options):
        calls.append(options)
        for message in messages:
            yield message
        if raises is not None:
            raise raises

    return patch('ichrisbirch.ai.assistants.anthropic.query', fake_query), calls


class TestOptions:
    def test_a_call_loads_nothing_from_disk_and_has_no_tools(self):
        options = make_assistant().options(max_tokens=8192, output_format=None)
        assert options.setting_sources == [], 'a CLAUDE.md in the working directory would reach the model'
        assert options.tools == []
        assert options.allowed_tools == []

    def test_named_tools_are_the_only_tools_and_need_no_permission_prompt(self):
        options = make_assistant(tools=['WebSearch']).options(max_tokens=8192, output_format=None)
        assert options.tools == ['WebSearch']
        assert options.allowed_tools == ['WebSearch']

    def test_the_subscription_token_and_the_output_cap_reach_the_cli(self):
        options = make_assistant(token='sk-ant-oat01-example').options(max_tokens=2048, output_format=None)
        assert options.env == {'CLAUDE_CODE_OAUTH_TOKEN': 'sk-ant-oat01-example', 'CLAUDE_CODE_MAX_OUTPUT_TOKENS': '2048'}
        assert options.model == 'claude-sonnet-4-6'

    def test_thinking_is_off_and_no_session_is_kept(self):
        options = make_assistant().options(max_tokens=8192, output_format=None)
        assert options.thinking == {'type': 'disabled'}
        assert options.extra_args == {'no-session-persistence': None}


class TestGenerate:
    @pytest.mark.asyncio
    async def test_a_complete_reply_is_returned(self):
        session, _ = stub_session(result_message(result='all of it'))
        with session:
            assert await make_assistant().generate('go') == 'all of it'

    @pytest.mark.asyncio
    async def test_a_reply_with_no_text_is_invalid_output(self):
        session, _ = stub_session(result_message(result=None))
        with session, pytest.raises(AssistantOutputError) as caught:
            await make_assistant().generate('go')
        assert caught.value.reason == AssistantFailure.INVALID_OUTPUT


class TestGenerateStructured:
    @pytest.mark.asyncio
    async def test_the_reply_is_validated_into_the_model_and_the_schema_reaches_the_cli(self):
        session, calls = stub_session(result_message(structured_output={'summary': 'short', 'tags': ['a']}))
        with session:
            reply = await make_assistant().generate_structured('go', Reply)
        assert reply == Reply(summary='short', tags=['a'])
        assert calls[0].output_format == {'type': 'json_schema', 'schema': Reply.model_json_schema()}

    @pytest.mark.asyncio
    async def test_no_structured_output_is_invalid_output(self):
        session, _ = stub_session(result_message(structured_output=None, result='I could not do that'))
        with session, pytest.raises(AssistantOutputError) as caught:
            await make_assistant().generate_structured('go', Reply)
        assert caught.value.reason == AssistantFailure.INVALID_OUTPUT
        assert caught.value.raw_output == 'I could not do that'

    @pytest.mark.asyncio
    async def test_output_a_model_validator_refuses_is_invalid_output(self):
        """The JSON Schema cannot carry a model validator, so Pydantic checks the reply again."""
        session, _ = stub_session(result_message(structured_output={'summary': 'short', 'tags': []}))
        with session, pytest.raises(AssistantOutputError) as caught:
            await make_assistant().generate_structured('go', Reply)
        assert caught.value.reason == AssistantFailure.INVALID_OUTPUT
        assert caught.value.raw_output == '{"summary": "short", "tags": []}'

    @pytest.mark.asyncio
    async def test_exhausted_schema_retries_are_invalid_output(self):
        session, _ = stub_session(raises=result_error('schema retries exhausted', subtype='error_max_structured_output_retries'))
        with session, pytest.raises(AssistantOutputError) as caught:
            await make_assistant().generate_structured('go', Reply)
        assert caught.value.reason == AssistantFailure.INVALID_OUTPUT


class TestFailures:
    @pytest.mark.asyncio
    async def test_a_reply_stopped_at_the_cap_raises_rather_than_returning_a_fragment(self):
        text = "API Error: Claude's response exceeded the 64 output token maximum."
        session, _ = stub_session(assistant_error('max_output_tokens'), raises=result_error(text))
        with session, pytest.raises(AssistantOutputError) as caught:
            await make_assistant().generate('go', max_tokens=64)
        assert caught.value.reason == AssistantFailure.TRUNCATED
        assert caught.value.raw_output == text
        assert '64' in str(caught.value), 'the cap that was hit belongs in the message'

    @pytest.mark.asyncio
    async def test_the_error_message_stays_short_enough_to_record(self):
        """Callers write str(e) to a database column and a Redis payload."""
        text = 'API Error: ' + 'x' * 10_000
        session, _ = stub_session(raises=result_error(text, api_error_status=500))
        with session, pytest.raises(AssistantOutputError) as caught:
            await make_assistant().generate('go')
        assert caught.value.reason == AssistantFailure.FAILED
        assert len(str(caught.value)) < 250
        assert caught.value.raw_output == text

    @pytest.mark.asyncio
    async def test_a_rejected_limit_is_a_usage_limit_with_its_reset_time(self):
        resets_at = dt.datetime(2026, 9, 18, 3, 0, tzinfo=dt.UTC)
        session, _ = stub_session(
            rate_limit('rejected', resets_at=int(resets_at.timestamp()), limit_type='seven_day'),
            assistant_error('rate_limit'),
            raises=result_error("You've hit your weekly limit", api_error_status=429),
        )
        with session, pytest.raises(AssistantUsageLimitReached) as caught:
            await make_assistant().generate('go')
        assert caught.value.resets_at == resets_at
        assert caught.value.limit_type == 'seven_day'

    @pytest.mark.asyncio
    async def test_a_rate_limit_error_without_a_reset_time_is_still_a_usage_limit(self):
        """Claude Code retries a passing 429 itself, so one that ends the session is the plan limit."""
        session, _ = stub_session(assistant_error('rate_limit'), raises=result_error('Request rejected (429)', api_error_status=429))
        with session, pytest.raises(AssistantUsageLimitReached) as caught:
            await make_assistant().generate('go')
        assert caught.value.resets_at is None

    @pytest.mark.asyncio
    async def test_a_limit_warning_does_not_stop_a_reply(self):
        session, _ = stub_session(rate_limit('allowed_warning', resets_at=1_789_666_200), result_message(result='still fine'))
        with session:
            assert await make_assistant().generate('go') == 'still fine'

    @pytest.mark.asyncio
    async def test_an_error_result_without_an_exception_still_fails(self):
        session, _ = stub_session(result_message(is_error=True, result='API Error: overloaded', api_error_status=529))
        with session, pytest.raises(AssistantOutputError) as caught:
            await make_assistant().generate('go')
        assert caught.value.reason == AssistantFailure.FAILED

    @pytest.mark.asyncio
    async def test_a_session_that_never_starts_fails(self):
        session, _ = stub_session(raises=CLINotFoundError('Claude Code not found'))
        with session, pytest.raises(AssistantOutputError) as caught:
            await make_assistant().generate('go')
        assert caught.value.reason == AssistantFailure.FAILED


class TestRealClaudeCode:
    @pytest.mark.asyncio
    async def test_the_cli_accepts_every_flag_and_reaches_the_api(self, monkeypatch: pytest.MonkeyPatch, tmp_path):
        """A refused token ends the session at the API, after every flag has been parsed.

        An unknown flag fails before any request, and carries no HTTP status. The
        empty home directory keeps a login on this machine from answering instead.
        """
        for name in [name for name in os.environ if name.startswith(('ANTHROPIC', 'CLAUDE'))]:
            monkeypatch.delenv(name)
        monkeypatch.setenv('HOME', str(tmp_path))

        with pytest.raises(AssistantOutputError) as caught:
            await make_assistant(token='sk-ant-oat01-refused-by-the-api').generate_structured('Say ok.', Reply, max_tokens=64)

        assert caught.value.reason == AssistantFailure.FAILED
        assert isinstance(caught.value.__cause__, ResultError)
        assert caught.value.__cause__.api_error_status == 401
