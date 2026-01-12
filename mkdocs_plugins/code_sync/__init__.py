"""Code synchronization tools for documentation.

This package provides tools for synchronizing code snippets in documentation
with actual source code files. Supports both AST-based element references
(for Python) and line-based references.

Usage in Markdown:
    # AST-based (Python functions, classes, methods):
    ```python file=path/to/file.py element=function_name
    # Content auto-replaced
    ```

    # Line-based (any file type):
    ```python file=path/to/file.py lines=10-20
    # Content auto-replaced
    ```

CLI Usage:
    python -m mkdocs_plugins.code_sync docs --base-path .
    python -m mkdocs_plugins.code_sync docs --base-path . --check

MkDocs Plugin:
    The MkDocs plugin is available in mkdocs_plugins.code_sync.plugin
    when mkdocs is installed.
"""

from .ast_parser import CodeElement
from .ast_parser import CodeParser
from .tool import CodeSyncTool
from .tool import MarkdownCodeReference

__all__ = ['CodeSyncTool', 'CodeParser', 'CodeElement', 'MarkdownCodeReference']
