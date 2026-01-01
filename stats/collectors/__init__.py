"""Collector runners for post-commit stats collection.

This module provides dynamic discovery of all collector modules.
Each collector module must have a `run(branch, project, ...)` function.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable
from contextlib import suppress
from typing import Any


def discover_collectors() -> dict[str, Callable[..., Any]]:
    """Discover all available collector modules.

    Returns:
        Dictionary mapping collector names to their run functions.
    """
    collectors: dict[str, Any] = {}

    import stats.collectors as collectors_package

    for _importer, modname, _ispkg in pkgutil.iter_modules(collectors_package.__path__):
        if modname.startswith('_'):
            continue
        with suppress(ImportError):
            module = importlib.import_module(f'stats.collectors.{modname}')
            if hasattr(module, 'run'):
                collectors[modname] = module.run

    return collectors


def get_collector(name: str) -> Callable[..., Any] | None:
    """Get a specific collector runner by name.

    Args:
        name: Name of the collector (e.g., 'tokei', 'pytest_collector')

    Returns:
        The collector's run function, or None if not found.
    """
    with suppress(ImportError):
        module = importlib.import_module(f'stats.collectors.{name}')
        if hasattr(module, 'run'):
            return module.run
    return None
