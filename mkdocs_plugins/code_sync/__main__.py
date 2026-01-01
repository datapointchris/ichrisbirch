"""CLI entry point for code_sync.

Usage:
    python -m mkdocs_plugins.code_sync docs --base-path .
    python -m mkdocs_plugins.code_sync docs --base-path . --check
"""

from .tool import main

if __name__ == '__main__':
    raise SystemExit(main())
