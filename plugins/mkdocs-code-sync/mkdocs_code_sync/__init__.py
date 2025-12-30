"""MkDocs plugin for synchronizing code snippets with the actual codebase.

This plugin scans Markdown files for code blocks with special annotations
and replaces them with current code from the specified files. Supports both
AST-based element references (for Python) and line-based references.

Usage in Markdown:
    # AST-based (Python functions, classes, methods):
    ```python file=path/to/file.py element=function_name
    # Content auto-replaced
    ```

    # Line-based (any file type):
    ```python file=path/to/file.py lines=10-20
    # Content auto-replaced
    ```
"""

import logging
import os
import sys
from pathlib import Path

from mkdocs.config.config_options import Type
from mkdocs.plugins import BasePlugin

# Add the project root to the path so we can import tools.code_sync
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tools.code_sync.code_sync import CodeSyncTool  # noqa: E402


class CodeSyncPlugin(BasePlugin):
    """MkDocs plugin that synchronizes code snippets in documentation with actual code files.

    Supports two reference styles:
    1. AST-based: ```python file=path.py element=function_name
       Best for Python code - survives refactoring
    2. Line-based: ```python file=path.py lines=10-20
       Works for any file type

    Additional options (for MkDocs-specific formatting):
    - label: Add a title to the code block (becomes title= in output)
    """

    config_scheme = (
        ('enabled', Type(bool, default=True)),
        ('base_path', Type(str, default='')),
    )

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.syncer = None
        self.base_path = ''

    def on_config(self, config):
        """Called when the config is loaded."""
        if not self.config.get('enabled', True):
            return config

        base_path = self.config.get('base_path', '')

        if base_path and not os.path.isabs(base_path):
            base_path = str(Path(config['docs_dir'], base_path))

        if not base_path:
            base_path = str(Path(config['docs_dir']).parent)

        self.base_path = base_path
        self.syncer = CodeSyncTool(base_path=base_path)

        return config

    def on_page_markdown(self, markdown, page, config, files):
        """Called when the Markdown for a page is loaded.

        Args:
            markdown: The page Markdown
            page: The page object
            config: The global config
            files: The files collection

        Returns:
            Updated Markdown with synchronized code snippets
        """
        if not self.config.get('enabled', True) or not self.syncer:
            return markdown

        # Extract all code references from the markdown
        references = self.syncer.extract_code_references(markdown)
        if not references:
            return markdown

        new_content = markdown
        offset = 0

        for ref in sorted(references, key=lambda r: r.start_pos):
            file_path = self.syncer.resolve_file_path(ref.file_path)

            # Get code content based on reference type
            if ref.is_line_based:
                code_content = self.syncer._extract_lines(file_path, ref.lines[0], ref.lines[1])
                if code_content is None:
                    self.logger.warning(f'Could not extract lines {ref.lines[0]}-{ref.lines[1]} from {file_path}')
                    continue
            else:
                code_element = self.syncer.parser.find_code_element(file_path, ref.element_name)
                if not code_element:
                    self.logger.warning(f"Code element '{ref.element_name}' not found in {file_path}")
                    continue
                code_content = code_element.code

            # Create replacement with proper formatting
            replacement = self._create_replacement(ref, code_content)

            # Update content
            start_pos = ref.start_pos + offset
            end_pos = ref.end_pos + offset
            new_content = new_content[:start_pos] + replacement + new_content[end_pos:]

            offset += len(replacement) - (end_pos - start_pos)

        return new_content

    def _create_replacement(self, ref, code_content: str) -> str:
        """Create the replacement text for a code reference."""
        if not ref.original_text.startswith('```'):
            # Inline reference - return as-is
            return ref.original_text

        # Build attributes for the code block
        attrs = []

        # Include the label as title if present
        if 'label' in ref.attrs:
            label = ref.attrs['label'].strip('"\'')
            attrs.append(f'title="{label}"')

        attr_str = ' '.join(attrs)
        if attr_str:
            attr_str = ' ' + attr_str

        return f'```{ref.language}{attr_str}\n{code_content}\n```'


# Entry point for the MkDocs plugin
entry_point = CodeSyncPlugin
