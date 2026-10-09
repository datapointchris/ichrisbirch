"""Tests for settings in the ichrisbirch.config module."""

import re

import pytest

from ichrisbirch.config import AISettings

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
