"""Pre-commit validation hooks.

This package contains validation tools that run during pre-commit:
- validate_html.py: HTML validation against W3C standards
- validate_markdown_links.py: Check markdown links resolve to existing files
- pytest_affected.py: Run tests for staged files only (fail-fast)
"""
