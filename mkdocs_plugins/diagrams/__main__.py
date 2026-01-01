"""CLI entry point for diagrams.

Usage:
    python -m mkdocs_plugins.diagrams
    python -m mkdocs_plugins.diagrams --force
"""

from .generate import main

if __name__ == '__main__':
    main()
