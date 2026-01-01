"""Tests for hook discovery mechanism."""

from __future__ import annotations


class TestHookDiscovery:
    """Tests for hook discovery."""

    def test_discover_hooks_finds_all_hooks(self) -> None:
        """Test that discover_hooks finds all implemented hooks."""
        from stats.hooks import discover_hooks

        hooks = discover_hooks()

        expected_hooks = {'ruff', 'mypy', 'bandit', 'shellcheck', 'codespell'}
        assert expected_hooks.issubset(set(hooks.keys()))

    def test_discovered_hooks_are_callable(self) -> None:
        """Test that discovered hooks are callable."""
        from stats.hooks import discover_hooks

        hooks = discover_hooks()

        for name, hook_fn in hooks.items():
            assert callable(hook_fn), f'{name} hook is not callable'

    def test_get_hook_returns_hook(self) -> None:
        """Test that get_hook returns a hook by name."""
        from stats.hooks import get_hook

        ruff_hook = get_hook('ruff')
        assert ruff_hook is not None
        assert callable(ruff_hook)

    def test_get_hook_returns_none_for_unknown(self) -> None:
        """Test that get_hook returns None for unknown hooks."""
        from stats.hooks import get_hook

        unknown_hook = get_hook('nonexistent_hook')
        assert unknown_hook is None
