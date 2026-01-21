"""Configuration loading from pyproject.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

# Default configuration if [tool.devstats] is not present
DEFAULT_CONFIG: dict[str, Any] = {
    'project': 'ichrisbirch',
    'events_path': 'stats/events/events.jsonl',
    'capture': {
        'hooks': ['ruff', 'mypy', 'bandit', 'shellcheck', 'codespell', 'detect_private_key', 'sass'],
    },
    'collect': {
        'collectors': ['tokei', 'pytest_collector', 'coverage', 'docker', 'dependencies', 'files'],
        'pytest_json_path': '/tmp/ichrisbirch-pytest-report.json',  # nosec B108
    },
}


def find_pyproject() -> Path:
    """Find pyproject.toml by walking up from current directory.

    Returns:
        Path to pyproject.toml

    Raises:
        FileNotFoundError: If pyproject.toml is not found
    """
    current = Path.cwd()
    while current != current.parent:
        pyproject = current / 'pyproject.toml'
        if pyproject.exists():
            return pyproject
        current = current.parent
    raise FileNotFoundError('pyproject.toml not found')


def load_config() -> dict[str, Any]:
    """Load devstats configuration from pyproject.toml.

    If [tool.devstats] section is not present, returns default configuration.
    Missing keys are filled in from defaults.

    Returns:
        Configuration dictionary
    """
    try:
        pyproject_path = find_pyproject()
    except FileNotFoundError:
        return DEFAULT_CONFIG.copy()

    with pyproject_path.open('rb') as f:
        data = tomllib.load(f)

    user_config = data.get('tool', {}).get('devstats', {})

    # Merge with defaults (user config takes precedence)
    config = DEFAULT_CONFIG.copy()
    config.update(user_config)

    # Merge nested dicts for capture and collect
    for key in ('capture', 'collect'):
        default_nested = DEFAULT_CONFIG.get(key, {})
        user_nested = user_config.get(key, {})
        config[key] = {**default_nested, **user_nested}

    return config
