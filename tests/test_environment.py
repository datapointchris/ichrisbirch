import subprocess
from pathlib import Path

import pytest

from tests import environment
from tests.environment import REPO_ROOT
from tests.environment import DockerComposeTestEnvironment
from tests.utils.database import test_settings


@pytest.fixture
def initializations(monkeypatch):
    calls = []
    monkeypatch.setattr(environment, 'full_initialization', calls.append)
    monkeypatch.setattr(DockerComposeTestEnvironment, 'docker_test_services_already_running', lambda self: True)
    monkeypatch.setattr(DockerComposeTestEnvironment, 'verify_test_services', lambda self: None)
    return calls


def test_another_checkouts_stack_ends_the_session_before_the_database_is_touched(monkeypatch, initializations):
    monkeypatch.setattr(environment, 'checkouts_that_started_the_test_stack', lambda: {Path('/elsewhere/ichrisbirch')})
    with pytest.raises(pytest.exit.Exception) as ended:
        DockerComposeTestEnvironment(test_settings).setup()
    assert 'started from /elsewhere/ichrisbirch' in str(ended.value)
    assert initializations == []


@pytest.mark.parametrize('checkouts', [{REPO_ROOT}, set()], ids=['this-checkout', 'no-containers'])
def test_a_stack_this_checkout_may_use_is_initialized(monkeypatch, initializations, checkouts):
    monkeypatch.setattr(environment, 'checkouts_that_started_the_test_stack', lambda: checkouts)
    DockerComposeTestEnvironment(test_settings).setup()
    assert initializations == [test_settings]


def test_the_checkouts_are_read_off_every_test_container(monkeypatch):
    labels = f'{REPO_ROOT}\n{REPO_ROOT}\n/elsewhere/ichrisbirch\n'
    monkeypatch.setattr(subprocess, 'run', lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, stdout=labels, stderr=''))
    assert environment.checkouts_that_started_the_test_stack() == {REPO_ROOT, Path('/elsewhere/ichrisbirch')}
