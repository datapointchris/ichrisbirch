"""CLI entry point for code_sync.

Usage:
    python -m tools.code_sync docs --base-path .
    python -m tools.code_sync docs --base-path . --check
"""

from .code_sync import main

if __name__ == '__main__':
    raise SystemExit(main())
