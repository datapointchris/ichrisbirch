"""AST-based code synchronization tool for documentation.

This tool uses AST (Abstract Syntax Tree) parsing to find and extract code snippets by their identifier (function/class/method name) rather
than by line numbers or special markers. It then updates references in markdown documentation files to keep them in sync with the code.
"""

import argparse
import logging
import re
import sys
from pathlib import Path

from .ast_parser import CodeParser

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class MarkdownCodeReference:
    """Represents a code reference in a markdown file."""

    def __init__(
        self,
        file_path: str,
        element_name: str | None = None,
        lines: tuple[int, int] | None = None,
        language: str = 'python',
        start_pos: int = 0,
        end_pos: int = 0,
        original_text: str = '',
        attrs: dict[str, str] | None = None,
    ):
        self.file_path = file_path
        self.element_name = element_name
        self.lines = lines
        self.language = language
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.original_text = original_text
        self.attrs = attrs or {}

    @property
    def is_line_based(self) -> bool:
        """Return True if this is a line-based reference."""
        return self.lines is not None

    def __repr__(self) -> str:
        if self.is_line_based:
            return f'MarkdownCodeReference(file_path={self.file_path}, lines={self.lines})'
        return f'MarkdownCodeReference(file_path={self.file_path}, element_name={self.element_name})'


class CodeSyncTool:
    """Tool that synchronizes code snippets in documentation with actual code files."""

    def __init__(self, base_path: str | Path | None = None):
        """Initialize the code synchronization tool.

        Args:
            base_path: Optional base path for resolving relative file paths
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.parser = CodeParser()

        self._code_block_element_pattern = re.compile(
            r'```([\w-]*)\s+'
            r'(?:code|file)=([^\s]+)\s+'
            r'(?:element|name)=([^\s]+)'
            r'(?:\s+([^\n]*))?'
            r'\n'
            r'(.*?)'
            r'```',
            re.DOTALL,
        )

        self._code_block_lines_pattern = re.compile(
            r'```([\w-]*)\s+'
            r'(?:code|file)=([^\s]+)\s+'
            r'lines=(\d+)-(\d+)'
            r'(?:\s+([^\n]*))?'
            r'\n'
            r'(.*?)'
            r'```',
            re.DOTALL,
        )

        self._inline_code_pattern = re.compile(
            r'\[code:'
            r'(?:code|file)=([^\s:]+):'
            r'(?:element|name)=([^\s:\]]+)'
            r'(?::([^\]]*))?\]'
        )

        self._inline_lines_pattern = re.compile(
            r'\[code:'
            r'(?:code|file)=([^\s:]+):'
            r'lines=(\d+)-(\d+)'
            r'(?::([^\]]*))?\]'
        )

    def find_markdown_files(self, directory: str | Path) -> list[Path]:
        """Find all markdown files in a directory (recursively).

        Args:
            directory: Path to the directory to search

        Returns:
            List of paths to markdown files
        """
        directory = Path(directory)
        if not directory.exists() or not directory.is_dir():
            logger.error(f'Directory not found or not a directory: {directory}')
            return []

        markdown_files = list(directory.glob('**/*.md'))
        logger.info(f'Found {len(markdown_files)} markdown files in {directory}')
        return markdown_files

    def extract_code_references(self, markdown_content: str) -> list[MarkdownCodeReference]:
        """Extract code references from markdown content.

        Args:
            markdown_content: Markdown content to parse

        Returns:
            List of code references found
        """
        references = []

        for match in self._code_block_element_pattern.finditer(markdown_content):
            language = match.group(1) or 'python'
            file_path = match.group(2)
            element_name = match.group(3)
            attrs_text = match.group(4) or ''

            attrs = self._parse_attrs(attrs_text)

            ref = MarkdownCodeReference(
                file_path=file_path,
                element_name=element_name,
                language=language,
                start_pos=match.start(),
                end_pos=match.end(),
                original_text=match.group(0),
                attrs=attrs,
            )
            references.append(ref)

        for match in self._code_block_lines_pattern.finditer(markdown_content):
            language = match.group(1) or ''
            file_path = match.group(2)
            start_line = int(match.group(3))
            end_line = int(match.group(4))
            attrs_text = match.group(5) or ''

            attrs = self._parse_attrs(attrs_text)

            ref = MarkdownCodeReference(
                file_path=file_path,
                lines=(start_line, end_line),
                language=language,
                start_pos=match.start(),
                end_pos=match.end(),
                original_text=match.group(0),
                attrs=attrs,
            )
            references.append(ref)

        for match in self._inline_code_pattern.finditer(markdown_content):
            file_path = match.group(1)
            element_name = match.group(2)
            attrs_text = match.group(3) or ''

            attrs = self._parse_attrs(attrs_text, separator=':')

            ref = MarkdownCodeReference(
                file_path=file_path,
                element_name=element_name,
                language='',
                start_pos=match.start(),
                end_pos=match.end(),
                original_text=match.group(0),
                attrs=attrs,
            )
            references.append(ref)

        for match in self._inline_lines_pattern.finditer(markdown_content):
            file_path = match.group(1)
            start_line = int(match.group(2))
            end_line = int(match.group(3))
            attrs_text = match.group(4) or ''

            attrs = self._parse_attrs(attrs_text, separator=':')

            ref = MarkdownCodeReference(
                file_path=file_path,
                lines=(start_line, end_line),
                language='',
                start_pos=match.start(),
                end_pos=match.end(),
                original_text=match.group(0),
                attrs=attrs,
            )
            references.append(ref)

        return references

    def _parse_attrs(self, attrs_text: str, separator: str = ' ') -> dict[str, str]:
        """Parse attribute string into a dictionary."""
        attrs = {}
        if attrs_text:
            for attr in attrs_text.split(separator):
                if '=' in attr:
                    key, value = attr.split('=', 1)
                    attrs[key.strip()] = value.strip()
        return attrs

    def resolve_file_path(self, file_path: str, markdown_file: Path | None = None) -> Path:
        """Resolve file path relative to base path or markdown file.

        Args:
            file_path: Path to resolve
            markdown_file: Optional path to the markdown file for relative path resolution

        Returns:
            Resolved absolute path
        """
        if Path(file_path).is_absolute():
            return Path(file_path)

        if markdown_file is not None:
            md_dir = markdown_file.parent
            candidate = md_dir / file_path
            if candidate.exists():
                return candidate

        candidate = self.base_path / file_path
        if candidate.exists():
            return candidate

        return self.base_path / file_path

    def sync_markdown_file(self, markdown_file: str | Path) -> bool:
        """Synchronize code snippets in a markdown file.

        Args:
            markdown_file: Path to the markdown file

        Returns:
            True if the file was modified, False otherwise
        """
        markdown_file = Path(markdown_file)
        if not markdown_file.exists():
            logger.error(f'Markdown file not found: {markdown_file}')
            return False

        try:
            content = markdown_file.read_text(encoding='utf-8')

            references = self.extract_code_references(content)
            if not references:
                logger.debug(f'No code references found in {markdown_file}')
                return False

            logger.info(f'Found {len(references)} code references in {markdown_file}')

            new_content = content
            offset = 0

            for ref in sorted(references, key=lambda r: r.start_pos):
                file_path = self.resolve_file_path(ref.file_path, markdown_file)

                if ref.is_line_based and ref.lines is not None:
                    code_content = self._extract_lines(file_path, ref.lines[0], ref.lines[1])
                    if code_content is None:
                        logger.warning(f'Could not extract lines {ref.lines[0]}-{ref.lines[1]} from {file_path}')
                        continue
                elif ref.element_name is not None:
                    code_element = self.parser.find_code_element(file_path, ref.element_name)
                    if not code_element:
                        logger.warning(f"Code element '{ref.element_name}' not found in {file_path}")
                        continue
                    code_content = code_element.code
                else:
                    logger.warning(f'Invalid reference in {markdown_file}: no element or lines specified')
                    continue

                replacement = self._create_replacement(ref, code_content)

                start_pos = ref.start_pos + offset
                end_pos = ref.end_pos + offset
                new_content = new_content[:start_pos] + replacement + new_content[end_pos:]

                offset += len(replacement) - (end_pos - start_pos)

            if new_content != content:
                markdown_file.write_text(new_content, encoding='utf-8')
                logger.info(f'Updated {markdown_file}')
                return True
            else:
                logger.debug(f'No changes needed for {markdown_file}')
                return False

        except Exception as e:
            logger.error(f'Error processing {markdown_file}: {e}')
            return False

    def _extract_lines(self, file_path: Path, start_line: int, end_line: int) -> str | None:
        """Extract specific lines from a file.

        Args:
            file_path: Path to the source file
            start_line: Starting line number (1-based, inclusive)
            end_line: Ending line number (1-based, inclusive)

        Returns:
            The extracted lines as a string, or None if extraction failed
        """
        if not file_path.exists():
            logger.error(f'File not found: {file_path}')
            return None

        try:
            lines = file_path.read_text(encoding='utf-8').splitlines(keepends=True)

            if start_line < 1 or end_line > len(lines) or start_line > end_line:
                logger.error(f'Invalid line range {start_line}-{end_line} for {file_path} ({len(lines)} lines)')
                return None

            extracted = lines[start_line - 1 : end_line]
            return ''.join(extracted).rstrip('\n')
        except Exception as e:
            logger.error(f'Error extracting lines from {file_path}: {e}')
            return None

    def _create_replacement(self, ref: MarkdownCodeReference, code_content: str) -> str:
        """Create the replacement text for a code reference.

        Args:
            ref: The code reference being replaced
            code_content: The code content to insert

        Returns:
            The formatted replacement string
        """
        if ref.original_text.startswith('```'):
            attrs_str = ' '.join(f'{k}={v}' for k, v in ref.attrs.items())
            if attrs_str:
                attrs_str = ' ' + attrs_str

            if ref.is_line_based and ref.lines is not None:
                return f'```{ref.language} file={ref.file_path} lines={ref.lines[0]}-{ref.lines[1]}{attrs_str}\n{code_content}\n```'
            else:
                return f'```{ref.language} file={ref.file_path} element={ref.element_name}{attrs_str}\n{code_content}\n```'
        else:
            attrs_str = ':'.join(f'{k}={v}' for k, v in ref.attrs.items())
            if attrs_str:
                attrs_str = ':' + attrs_str

            if ref.is_line_based and ref.lines is not None:
                return f'[code:file={ref.file_path}:lines={ref.lines[0]}-{ref.lines[1]}{attrs_str}]'
            else:
                return f'[code:file={ref.file_path}:element={ref.element_name}{attrs_str}]'

    def sync_all_markdown_files(self, directory: str | Path) -> tuple[int, int]:
        """Synchronize code snippets in all markdown files in a directory.

        Args:
            directory: Path to the directory containing markdown files

        Returns:
            Tuple of (number of files processed, number of files updated)
        """
        markdown_files = self.find_markdown_files(directory)
        updated_count = 0

        for md_file in markdown_files:
            if self.sync_markdown_file(md_file):
                updated_count += 1

        return len(markdown_files), updated_count


def main() -> int:
    """CLI entry point for code sync."""
    parser = argparse.ArgumentParser(
        description='Synchronize code snippets in markdown files using AST parsing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync all docs with code
  python -m mkdocs_plugins.code_sync docs --base-path .

  # Check if docs are in sync (CI mode)
  python -m mkdocs_plugins.code_sync docs --base-path . --check

  # Verbose output
  python -m mkdocs_plugins.code_sync docs --base-path . -v
""",
    )
    parser.add_argument('docs_dir', help='Directory containing markdown files')
    parser.add_argument('--base-path', '-b', help='Base path for resolving relative file paths')
    parser.add_argument('--check', '-c', action='store_true', help='Check if docs are in sync without modifying (exit 1 if changes needed)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    syncer = CodeSyncTool(args.base_path)

    if args.check:
        return _run_check_mode(syncer, args.docs_dir)
    else:
        processed, updated = syncer.sync_all_markdown_files(args.docs_dir)
        logger.info(f'Processed {processed} files, updated {updated} files')
        return 0


def _run_check_mode(syncer: CodeSyncTool, docs_dir: str) -> int:
    """Run in check mode - report if docs are out of sync without modifying."""
    import tempfile
    from pathlib import Path

    markdown_files = syncer.find_markdown_files(docs_dir)
    out_of_sync = []

    for md_file in markdown_files:
        original_content = md_file.read_text(encoding='utf-8')

        references = syncer.extract_code_references(original_content)
        if not references:
            continue

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp:
            tmp.write(original_content)
            tmp_path = Path(tmp.name)

        try:
            syncer.sync_markdown_file(tmp_path)
            synced_content = tmp_path.read_text(encoding='utf-8')

            if original_content != synced_content:
                out_of_sync.append(md_file)
                logger.warning(f'OUT OF SYNC: {md_file}')
        finally:
            tmp_path.unlink()

    if out_of_sync:
        logger.error(f'\n{len(out_of_sync)} file(s) are out of sync with source code:')
        for out_of_sync_file in out_of_sync:
            logger.error(f'  - {out_of_sync_file}')
        logger.error("\nRun 'python -m mkdocs_plugins.code_sync docs --base-path .' to sync them.")
        return 1
    else:
        logger.info(f'All {len(markdown_files)} markdown files are in sync!')
        return 0


if __name__ == '__main__':
    sys.exit(main())
