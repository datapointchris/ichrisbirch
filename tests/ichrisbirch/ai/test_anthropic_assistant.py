"""Unit tests for AnthropicAssistant — no network, no settings, no database."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ichrisbirch.ai.assistants.anthropic import AnthropicAssistant
from ichrisbirch.ai.assistants.anthropic import AssistantFailure
from ichrisbirch.ai.assistants.anthropic import AssistantOutputError


def _assistant() -> AnthropicAssistant:
    """Build one without touching Settings or constructing a real client."""
    settings = MagicMock()
    settings.ai.anthropic.api_key = 'test-key'
    settings.ai.anthropic.model = 'claude-test'
    with patch('ichrisbirch.ai.assistants.anthropic.Anthropic'):
        return AnthropicAssistant(name='Test Assistant', system_prompt='be brief', settings=settings)


def _response(text: str, stop_reason: str):
    block = MagicMock()
    block.type = 'text'
    block.text = text
    response = MagicMock()
    response.content = [block]
    response.stop_reason = stop_reason
    response.usage.input_tokens = 10
    response.usage.output_tokens = 20
    return response


class TestGenerate:
    def test_a_complete_reply_is_returned(self):
        assistant = _assistant()
        assistant.client.messages.create.return_value = _response('all of it', 'end_turn')
        assert assistant.generate('go') == 'all of it'

    def test_a_reply_stopped_at_the_cap_raises_rather_than_returning_a_fragment(self):
        assistant = _assistant()
        assistant.client.messages.create.return_value = _response('half of i', 'max_tokens')
        with pytest.raises(AssistantOutputError) as caught:
            assistant.generate('go', max_tokens=64)
        assert caught.value.reason == AssistantFailure.TRUNCATED
        assert caught.value.raw_output == 'half of i'
        assert '64' in str(caught.value), 'the cap that was hit belongs in the message'

    def test_the_error_message_stays_short_enough_to_record(self):
        """Callers write str(e) to a database column and a Redis payload."""
        assistant = _assistant()
        assistant.client.messages.create.return_value = _response('x' * 10_000, 'max_tokens')
        with pytest.raises(AssistantOutputError) as caught:
            assistant.generate('go', max_tokens=64)
        assert len(str(caught.value)) < 200
        assert len(caught.value.raw_output) == 10_000


class TestParseJsonObject:
    def test_a_plain_object_parses(self):
        assert AnthropicAssistant.parse_json_object('{"a": 1}', 'Test') == {'a': 1}

    def test_a_code_fenced_object_parses(self):
        assert AnthropicAssistant.parse_json_object('```json\n{"a": 1}\n```', 'Test') == {'a': 1}

    def test_prose_raises_not_json(self):
        with pytest.raises(AssistantOutputError) as caught:
            AnthropicAssistant.parse_json_object('I cannot do that', 'Test')
        assert caught.value.reason == AssistantFailure.NOT_JSON
        assert caught.value.raw_output == 'I cannot do that'

    def test_a_top_level_list_raises_not_an_object(self):
        """A list reaches .get in every caller, which raises AttributeError."""
        with pytest.raises(AssistantOutputError) as caught:
            AnthropicAssistant.parse_json_object('[1, 2]', 'Test')
        assert caught.value.reason == AssistantFailure.NOT_AN_OBJECT

    def test_the_assistant_name_reaches_the_message(self):
        with pytest.raises(AssistantOutputError) as caught:
            AnthropicAssistant.parse_json_object('nope', 'Article Insights')
        assert 'Article Insights' in str(caught.value)
