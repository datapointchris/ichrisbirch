"""Tests for settings in the life.config module."""

import re

import pytest

from life import config
from life.config import AISettings
from life.config import Settings
from tests import environment
from tests.environment import PrivateServices

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


def test_testing_without_postgres_host_refuses_to_load(monkeypatch: pytest.MonkeyPatch):
    """A test run never falls back to a checkout's .env, which on a workstation is the development one.

    The undecorated function runs, so the session's cached settings stay the ones its services point at.
    """
    monkeypatch.setenv('ENVIRONMENT', 'testing')
    monkeypatch.delenv('POSTGRES_HOST', raising=False)

    with pytest.raises(RuntimeError):
        config.get_settings.__wrapped__()


def test_private_services_point_settings_at_the_named_servers(monkeypatch: pytest.MonkeyPatch):
    """TEST_DATABASE_URL and TEST_REDIS_URL replace the containers, credentials and database included."""
    monkeypatch.setenv('TEST_DATABASE_URL', 'postgresql://ci%40user:p%2Fss@db.internal:6543/life_ci')
    monkeypatch.setenv('TEST_REDIS_URL', 'redis://:r%40dis@cache.internal:6380/3')
    initialized: list[Settings] = []
    monkeypatch.setattr(environment, 'full_initialization', initialized.append)
    settings = Settings()
    services = PrivateServices(settings)

    services.start()

    for database in (settings.postgres, settings.sqlalchemy):
        named = (database.host, database.port, database.username, database.password, database.database)
        assert named == ('db.internal', 6543, 'ci@user', 'p/ss', 'life_ci')
    assert (settings.redis.host, settings.redis.port, settings.redis.password, settings.redis.db) == ('cache.internal', 6380, 'r@dis', 3)
    assert services.started == []
    assert initialized == [settings]
