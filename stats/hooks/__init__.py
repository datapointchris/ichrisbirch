"""Hook runners for pre-commit tool captures.

This module provides dynamic discovery of all hook modules.
Each hook module must have a `run(staged_files, branch, project)` function.
"""

from __future__ import annotations

import importlib
import pkgutil
from contextlib import suppress
from typing import TYPE_CHECKING
from typing import Any
from typing import Protocol

if TYPE_CHECKING:
    from stats.schemas.base import BaseEvent


class HookRunner(Protocol):
    """Protocol for hook runner functions."""

    def __call__(self, staged_files: list[str], branch: str, project: str) -> BaseEvent: ...


def discover_hooks() -> dict[str, HookRunner]:
    """Discover all available hook modules.

    Returns:
        Dictionary mapping hook names to their run functions.
    """
    hooks: dict[str, Any] = {}

    import stats.hooks as hooks_package

    for _importer, modname, _ispkg in pkgutil.iter_modules(hooks_package.__path__):
        if modname.startswith('_'):
            continue
        with suppress(ImportError):
            module = importlib.import_module(f'stats.hooks.{modname}')
            if hasattr(module, 'run'):
                hooks[modname] = module.run

    return hooks


def get_hook(name: str) -> HookRunner | None:
    """Get a specific hook runner by name.

    Args:
        name: Name of the hook (e.g., 'ruff', 'mypy')

    Returns:
        The hook's run function, or None if not found.
    """
    with suppress(ImportError):
        module = importlib.import_module(f'stats.hooks.{name}')
        if hasattr(module, 'run'):
            return module.run  # type: ignore[return-value]
    return None
