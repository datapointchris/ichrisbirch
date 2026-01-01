"""Test fixtures for the AST code synchronization tool tests."""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def python_test_file(temp_dir):
    """Create a test Python file with sample functions and classes."""
    file_path = temp_dir / 'test_module.py'

    content = '''
def simple_function():
    """A simple function for testing."""
    return "Hello, world!"

class TestClass:
    """A test class with methods."""

    def __init__(self, value=None):
        self.value = value or "default"

    def test_method(self):
        """A test method."""
        return f"Value: {self.value}"

    def another_method(self, param):
        """Another test method with parameters."""
        return f"Value: {self.value}, Param: {param}"

CONSTANT = "This is a constant"

# A comment that should not be parsed as a code element
'''

    file_path.write_text(content)

    return file_path


@pytest.fixture
def js_test_file(temp_dir):
    """Create a test JavaScript file with sample functions and classes."""
    file_path = temp_dir / 'test_module.js'

    content = """
function simpleFunction() {
    // A simple function for testing
    return "Hello, world!";
}

class TestClass {
    constructor(value=null) {
        this.value = value || "default";
    }

    testMethod() {
        // A test method
        return `Value: ${this.value}`;
    }

    anotherMethod(param) {
        // Another test method with parameters
        return `Value: ${this.value}, Param: ${param}`;
    }
}

const CONSTANT = "This is a constant";

// A comment that should not be parsed as a code element
"""

    file_path.write_text(content)

    return file_path


@pytest.fixture
def markdown_test_file(temp_dir, python_test_file):
    """Create a test markdown file with code references."""
    file_path = temp_dir / 'test_doc.md'
    rel_python_path = os.path.relpath(python_test_file, temp_dir)

    content = f"""# Test Documentation

This is a test markdown file with code references.

## Code Block Reference

```python file={rel_python_path} element=simple_function
# This content will be replaced
```

## Another Code Block Reference

```python file={rel_python_path} element=TestClass.test_method
# This content will be replaced
```

## Inline Reference

Here's an inline reference: [code:file={rel_python_path}:element=CONSTANT]

That's all for now!
"""

    file_path.write_text(content)

    return file_path


@pytest.fixture
def nested_markdown_test_file(temp_dir, python_test_file):
    """Create a nested directory with a markdown file for testing path resolution."""
    nested_dir = temp_dir / 'nested'
    nested_dir.mkdir()

    file_path = nested_dir / 'nested_doc.md'
    rel_python_path = os.path.relpath(python_test_file, nested_dir)

    content = f"""# Nested Test Documentation

This is a test markdown file in a nested directory.

## Code Block Reference

```python file={rel_python_path} element=simple_function
# This content will be replaced
```

That's all for now!
"""

    file_path.write_text(content)

    return file_path
