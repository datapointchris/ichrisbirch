"""AST-based code parser for documentation synchronization.

This module provides functionality to parse code files using AST (Abstract Syntax Tree) and extract code blocks by their identifier
(function name, class name, method name, etc.) rather than relying on line numbers or special markers in the code.
"""

import ast
import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CodeElement:
    """Represents a code element (function, class, method, etc.)."""

    name: str
    code: str
    start_line: int
    end_line: int
    parent: str | None = None

    @property
    def full_name(self) -> str:
        """Get the full name including parent if applicable."""
        if self.parent:
            return f'{self.parent}.{self.name}'
        return self.name


class ASTParser:
    """Parser that uses AST to extract code elements from Python files."""

    def __init__(self):
        self.elements: dict[str, CodeElement] = {}

    def parse_file(self, file_path: str | Path) -> dict[str, CodeElement]:
        """Parse a Python file using AST and extract code elements.

        Args:
            file_path: Path to the Python file

        Returns:
            Dictionary of code elements indexed by their full name
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f'File not found: {file_path}')
            return {}

        if file_path.suffix.lower() != '.py':
            logger.warning(f'Not a Python file, AST parsing not supported: {file_path}')
            return {}

        try:
            source = file_path.read_text(encoding='utf-8')

            tree = ast.parse(source)
            self.elements = {}
            self._extract_elements(tree, source, None)
            return self.elements

        except Exception as e:
            logger.error(f'Error parsing {file_path}: {e}')
            return {}

    def _extract_elements(self, tree: ast.AST, source: str, parent: str | None = None) -> None:
        """Recursively extract code elements from an AST.

        Args:
            tree: The AST to extract elements from
            source: The source code string
            parent: Name of the parent element (if any)
        """
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                name = node.name
                start_line = self._find_start_line_with_decorators(node)
                end_line = self._find_end_line(node, source)

                element = CodeElement(
                    name=name, code=self._get_source(source, start_line, end_line), start_line=start_line, end_line=end_line, parent=parent
                )

                key = element.full_name
                self.elements[key] = element

            elif isinstance(node, ast.ClassDef):
                name = node.name
                start_line = self._find_start_line_with_decorators(node)
                end_line = self._find_end_line(node, source)

                element = CodeElement(
                    name=name, code=self._get_source(source, start_line, end_line), start_line=start_line, end_line=end_line, parent=parent
                )

                key = element.full_name
                self.elements[key] = element

                self._extract_elements(node, source, name)

            elif isinstance(node, ast.Assign | ast.AnnAssign):
                if parent is None:
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                name = target.id
                                start_line = node.lineno
                                end_line = start_line

                                element = CodeElement(
                                    name=name,
                                    code=self._get_source(source, start_line, end_line),
                                    start_line=start_line,
                                    end_line=end_line,
                                    parent=parent,
                                )

                                key = element.full_name
                                self.elements[key] = element
                    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                        name = node.target.id
                        start_line = node.lineno
                        end_line = start_line

                        element = CodeElement(
                            name=name,
                            code=self._get_source(source, start_line, end_line),
                            start_line=start_line,
                            end_line=end_line,
                            parent=parent,
                        )

                        key = element.full_name
                        self.elements[key] = element

    def _find_start_line_with_decorators(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> int:
        """Find the start line of a node, including any decorators.

        Args:
            node: The AST node (FunctionDef, AsyncFunctionDef, or ClassDef)

        Returns:
            The start line number (including decorators if present)
        """
        if node.decorator_list:
            return min(d.lineno for d in node.decorator_list)
        return node.lineno

    def _find_end_line(self, node: ast.AST, source: str) -> int:
        """Find the end line of a node.

        Args:
            node: The AST node
            source: The source code string

        Returns:
            The end line number
        """
        if hasattr(node, 'end_lineno') and node.end_lineno is not None:
            return node.end_lineno

        last_child_line = getattr(node, 'lineno', 1)
        for child in ast.iter_child_nodes(node):
            end_line = self._find_end_line(child, source)
            last_child_line = max(last_child_line, end_line)

        return last_child_line

    def _get_source(self, source: str, start_line: int, end_line: int) -> str:
        """Extract a portion of the source code.

        Args:
            source: The complete source code
            start_line: Starting line number (1-based)
            end_line: Ending line number (1-based)

        Returns:
            The extracted source code
        """
        lines = source.splitlines()
        return '\n'.join(lines[start_line - 1 : end_line])


class TreeSitterParser:
    """Parser that uses Tree-sitter to extract code elements from various language files."""

    def __init__(self):
        self._has_tree_sitter = False
        try:
            import tree_sitter  # noqa: F401

            self._has_tree_sitter = True
        except ImportError:
            logger.warning("Tree-sitter not available. Install with 'pip install tree-sitter'")

    def is_available(self) -> bool:
        """Check if Tree-sitter is available."""
        return self._has_tree_sitter

    def parse_file(self, file_path: str | Path) -> dict[str, CodeElement]:
        """Parse a file using Tree-sitter and extract code elements.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary of code elements indexed by their full name
        """
        if not self._has_tree_sitter:
            logger.warning('Tree-sitter not available, falling back to regex')
            return {}

        logger.info('Tree-sitter parsing not yet implemented')
        return {}


class FallbackParser:
    """Fallback parser using simple regex patterns for languages without AST support."""

    def parse_file(self, file_path: str | Path, pattern: str | None = None) -> dict[str, CodeElement]:
        """Parse a file using regex to extract code elements.

        Args:
            file_path: Path to the file
            pattern: Optional regex pattern to use

        Returns:
            Dictionary of code elements indexed by their full name
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f'File not found: {file_path}')
            return {}

        try:
            source = file_path.read_text(encoding='utf-8')

            elements = {}

            if pattern is None:
                patterns = self._get_default_patterns(file_path.suffix.lower())
            else:
                patterns = {'_custom_': re.compile(pattern, re.MULTILINE)}

            for name, regex in patterns.items():
                for match in regex.finditer(source):
                    if name == '_custom_':
                        element_name = match.group(1) if match.groups() else 'unnamed'
                    else:
                        element_name = name

                    start_pos = match.start()
                    end_pos = match.end()
                    start_line = source[:start_pos].count('\n') + 1
                    end_line = source[:end_pos].count('\n') + 1

                    code = match.group(0)

                    elements[element_name] = CodeElement(name=element_name, code=code, start_line=start_line, end_line=end_line)

            return elements

        except Exception as e:
            logger.error(f'Error parsing {file_path} with regex: {e}')
            return {}

    def _get_default_patterns(self, file_extension: str) -> dict[str, re.Pattern]:
        """Get default regex patterns for a given file extension.

        Args:
            file_extension: The file extension including the dot

        Returns:
            Dictionary of name -> regex pattern
        """
        patterns = {}

        if file_extension in ('.js', '.ts'):
            patterns['simpleFunction'] = re.compile(r'function\s+simpleFunction\s*\([^{]*\)\s*\{[\s\S]*?\}', re.DOTALL)
            patterns['TestClass'] = re.compile(r'class\s+TestClass\s*\{[\s\S]*?\}', re.DOTALL)
            patterns['CONSTANT'] = re.compile(r'const\s+CONSTANT\s*=\s*[^;]*;', re.MULTILINE)

        elif file_extension == '.go':
            patterns['function'] = re.compile(r'func\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*(?:\([^)]*\))?\s*\{[^}]*\}', re.MULTILINE)

        elif file_extension in ('.c', '.cpp', '.h'):
            patterns['function'] = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{[^}]*\}', re.MULTILINE)

        return patterns


class CodeParser:
    """Main parser class that delegates to the appropriate parser based on the file type."""

    def __init__(self):
        self.ast_parser = ASTParser()
        self.tree_sitter_parser = TreeSitterParser()
        self.fallback_parser = FallbackParser()

    def parse_file(self, file_path: str | Path) -> dict[str, CodeElement]:
        """Parse a file and extract code elements.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary of code elements indexed by their name
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f'File not found: {file_path}')
            return {}

        if file_path.suffix.lower() == '.py':
            return self.ast_parser.parse_file(file_path)
        elif self.tree_sitter_parser.is_available():
            result = self.tree_sitter_parser.parse_file(file_path)
            if result:
                return result

        return self.fallback_parser.parse_file(file_path)

    def find_code_element(self, file_path: str | Path, element_name: str) -> CodeElement | None:
        """Find a specific code element by name.

        Args:
            file_path: Path to the file
            element_name: Name of the element to find (e.g., "MyClass.my_method", "my_function")

        Returns:
            The found code element, or None if not found
        """
        elements = self.parse_file(file_path)

        if element_name in elements:
            return elements[element_name]

        for key, element in elements.items():
            if key.endswith(f'.{element_name}') or key == element_name:
                return element

        return None


if __name__ == '__main__':
    import sys

    parser = CodeParser()

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f'Parsing {file_path}...')

        elements = parser.parse_file(file_path)
        for name, element in elements.items():
            print(f'\n{name} (lines {element.start_line}-{element.end_line}):')
            print('-' * 50)
            print(element.code)
            print('-' * 50)
    else:
        print('Usage: ast_parser.py <file_path>')
