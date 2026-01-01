"""Tests for the code synchronization tool."""

import re
from pathlib import Path

from mkdocs_plugins.code_sync import CodeSyncTool


def test_markdown_code_reference_extraction(markdown_test_file):
    """Test extracting code references from markdown."""
    syncer = CodeSyncTool()

    content = markdown_test_file.read_text()

    references = syncer.extract_code_references(content)

    assert len(references) == 3

    block_refs = [r for r in references if r.original_text.startswith('```')]
    inline_refs = [r for r in references if not r.original_text.startswith('```')]

    assert len(block_refs) == 2
    assert len(inline_refs) == 1

    simple_function_ref = next((r for r in references if r.element_name == 'simple_function'), None)
    assert simple_function_ref is not None
    assert simple_function_ref.language == 'python'

    method_ref = next((r for r in references if r.element_name == 'TestClass.test_method'), None)
    assert method_ref is not None
    assert method_ref.language == 'python'

    constant_ref = next((r for r in references if r.element_name == 'CONSTANT'), None)
    assert constant_ref is not None


def test_file_path_resolution(temp_dir, python_test_file, nested_markdown_test_file):
    """Test resolving file paths relative to markdown files."""
    syncer = CodeSyncTool(base_path=temp_dir)

    nested_markdown = Path(nested_markdown_test_file)

    content = nested_markdown.read_text()

    references = syncer.extract_code_references(content)
    assert len(references) == 1

    resolved_path = syncer.resolve_file_path(references[0].file_path, nested_markdown)

    assert resolved_path.exists()
    assert resolved_path.samefile(python_test_file)


def test_markdown_file_sync(temp_dir, python_test_file, markdown_test_file):
    """Test synchronizing code snippets in a markdown file."""
    syncer = CodeSyncTool(base_path=temp_dir)

    updated = syncer.sync_markdown_file(markdown_test_file)
    assert updated is True

    updated_content = markdown_test_file.read_text()

    assert 'A simple function for testing' in updated_content
    assert 'return "Hello, world!"' in updated_content
    assert 'A test method' in updated_content
    assert 'Value: {self.value}' in updated_content

    assert re.search(r'\[code:file=.*?:element=CONSTANT\]', updated_content) is not None


def test_sync_all_markdown_files(temp_dir, python_test_file, markdown_test_file, nested_markdown_test_file):
    """Test synchronizing all markdown files in a directory."""
    syncer = CodeSyncTool(base_path=temp_dir)

    processed, updated = syncer.sync_all_markdown_files(temp_dir)

    assert processed == 2
    assert updated == 2

    main_content = markdown_test_file.read_text()

    nested_content = nested_markdown_test_file.read_text()

    assert 'A simple function for testing' in main_content
    assert 'A simple function for testing' in nested_content


def test_sync_with_missing_elements(temp_dir):
    """Test synchronizing when referenced code elements don't exist."""
    md_file = temp_dir / 'missing.md'
    py_file = temp_dir / 'empty.py'

    py_file.write_text('# Empty file')

    content = f"""# Test Missing Elements

```python file={py_file.name} element=nonexistent_function
# This should not be replaced
```
"""

    md_file.write_text(content)

    syncer = CodeSyncTool(base_path=temp_dir)
    updated = syncer.sync_markdown_file(md_file)

    assert updated is False

    updated_content = md_file.read_text()

    assert '# This should not be replaced' in updated_content
