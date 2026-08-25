"""Tests for settings in the ichrisbirch.config module."""

import re

import pytest

from ichrisbirch.config import AISettings
from ichrisbirch.config import env_bool

DATE_SUFFIXED_MODEL = re.compile(r'-20\d{6}$')


class TestAnthropicSettings:
    def test_default_model_is_a_tier_alias_not_a_dated_snapshot(self, monkeypatch: pytest.MonkeyPatch):
        """A dated id pins the deployment to one snapshot and stops tracking the tier it names."""
        monkeypatch.delenv('AI_ANTHROPIC_DEFAULT_MODEL', raising=False)

        model = AISettings.AnthropicSettings().model

        assert not DATE_SUFFIXED_MODEL.search(model), f'{model} pins the default to one snapshot'

    def test_environment_overrides_the_default_model(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv('AI_ANTHROPIC_DEFAULT_MODEL', 'claude-opus-5')

        assert AISettings.AnthropicSettings().model == 'claude-opus-5'


class TestEnvBool:
    """`bool(os.environ[...])` is true for any non-empty string, including "False"."""

    @pytest.mark.parametrize('raw', ['False', 'false', 'FALSE', ' false ', '0', 'no', 'off'])
    def test_falsey_spellings_read_as_false(self, raw: str, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv('SOME_FLAG', raw)

        assert env_bool('SOME_FLAG') is False

    @pytest.mark.parametrize('raw', ['True', 'true', 'TRUE', ' true ', '1', 'yes', 'on'])
    def test_truthy_spellings_read_as_true(self, raw: str, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv('SOME_FLAG', raw)

        assert env_bool('SOME_FLAG') is True

    def test_an_unrecognized_value_raises_rather_than_picking_a_side(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv('SOME_FLAG', 'maybe')

        with pytest.raises(ValueError, match='SOME_FLAG'):
            env_bool('SOME_FLAG')
