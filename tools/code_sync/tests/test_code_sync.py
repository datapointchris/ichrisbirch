"""Tests for the code synchronization tool."""

import re
from pathlib import Path

from tools.code_sync.code_sync import CodeSyncTool


def test_markdown_code_reference_extraction(markdown_test_file):
    """Test extracting code references from markdown."""
    syncer = CodeSyncTool()

    with open(markdown_test_file) as f:
        content = f.read()

    references = syncer.extract_code_references(content)

    # Check that the correct number of references were found
    assert len(references) == 3

    # Check that both code blocks and inline references were found
    block_refs = [r for r in references if r.original_text.startswith('```')]
    inline_refs = [r for r in references if not r.original_text.startswith('```')]

    assert len(block_refs) == 2
    assert len(inline_refs) == 1

    # Check specific references
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

    # Get the markdown file
    nested_markdown = Path(nested_markdown_test_file)

    with open(nested_markdown) as f:
        content = f.read()

    references = syncer.extract_code_references(content)
    assert len(references) == 1

    # Resolve the path to the python file
    resolved_path = syncer.resolve_file_path(references[0].file_path, nested_markdown)

    # Check that the path was resolved correctly
    assert resolved_path.exists()
    assert resolved_path.samefile(python_test_file)


def test_markdown_file_sync(temp_dir, python_test_file, markdown_test_file):
    """Test synchronizing code snippets in a markdown file."""
    syncer = CodeSyncTool(base_path=temp_dir)

    # Sync the markdown file
    updated = syncer.sync_markdown_file(markdown_test_file)
    assert updated is True

    # Read the updated markdown file
    with open(markdown_test_file) as f:
        updated_content = f.read()

    # Check that the code blocks were updated with the actual code
    assert 'A simple function for testing' in updated_content
    assert 'return "Hello, world!"' in updated_content
    assert 'A test method' in updated_content
    assert 'Value: {self.value}' in updated_content

    # Check that the inline reference is preserved
    assert re.search(r'\[code:file=.*?:element=CONSTANT\]', updated_content) is not None


def test_sync_all_markdown_files(temp_dir, python_test_file, markdown_test_file, nested_markdown_test_file):
    """Test synchronizing all markdown files in a directory."""
    syncer = CodeSyncTool(base_path=temp_dir)

    # Sync all markdown files in the directory
    processed, updated = syncer.sync_all_markdown_files(temp_dir)

    # Check that both markdown files were processed and updated
    assert processed == 2
    assert updated == 2

    # Read the updated files and check content
    with open(markdown_test_file) as f:
        main_content = f.read()

    with open(nested_markdown_test_file) as f:
        nested_content = f.read()

    # Check that code was updated in both files
    assert 'A simple function for testing' in main_content
    assert 'A simple function for testing' in nested_content


def test_sync_with_missing_elements(temp_dir):
    """Test synchronizing when referenced code elements don't exist."""
    # Create a markdown file referencing non-existent elements
    md_file = temp_dir / 'missing.md'
    py_file = temp_dir / 'empty.py'

    with open(py_file, 'w') as f:
        f.write('# Empty file')

    content = f"""# Test Missing Elements

```python file={py_file.name} element=nonexistent_function
# This should not be replaced
```
"""

    with open(md_file, 'w') as f:
        f.write(content)

    # Attempt to sync
    syncer = CodeSyncTool(base_path=temp_dir)
    updated = syncer.sync_markdown_file(md_file)

    # Should not update since the element doesn't exist
    assert updated is False

    # Content should be unchanged
    with open(md_file) as f:
        updated_content = f.read()

    assert '# This should not be replaced' in updated_content
