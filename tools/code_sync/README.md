# AST Code Sync

An intelligent code snippet synchronization tool that uses AST (Abstract Syntax Tree) parsing to extract code by name/identifier without requiring special markers in your codebase.

## Overview

This tool is designed to synchronize code snippets in your documentation with the actual codebase. Unlike traditional approaches that rely on line numbers or special markers in the source code, AST Code Sync uses abstract syntax tree parsing to locate code elements by their names (function, class, method names).

## Features

- **AST-based parsing**: Understands code structure rather than relying on line numbers
- **No special markers required**: Identifies code by name, not by comments or markers
- **Multiple language support**:
  - Python (using built-in `ast` module)
  - Other languages supported through Tree-sitter (optional dependency)
  - Fallback to regex patterns for languages without AST support
- **Pre-commit integration**: Automatically sync docs on commit
- **GitHub Actions workflow**: Keep documentation in sync with code on CI/CD

## Installation

No special installation is required since the tool is included directly in the repository. However, you may want to install optional dependencies:

```bash
# For improved multi-language support
pip install tree-sitter
```

## Usage

### In Markdown Documents

To reference code elements in your markdown, use one of these formats:

#### Code Block Format

```markdown
    ```python file=path/to/file.py element=function_name
    # This content will be replaced with the actual code
    ```
```

#### Inline Reference Format

```markdown
[code:file=path/to/file.py:element=MyClass.method_name]
```

### Command Line Usage

To manually run the tool:

```bash
python -m tools.ast-code-sync.code_sync docs --base-path .
```

### Pre-commit Hook

Add the following to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: ast-code-sync
        name: AST Code Sync
        description: "Synchronize code snippets in documentation using AST parsing"
        entry: python -m tools.ast-code-sync.code_sync
        language: python
        pass_filenames: false
        always_run: true
        args: ["docs", "--base-path", "."]
```

### GitHub Actions Integration

Copy the workflow file from `tools/ast-code-sync/github-workflow-sync-docs.yml` to your `.github/workflows/` directory.

## Migrating from old format

The old format used regex patterns like:

```markdown
```[path/to/file.py] (start_line-end_line)
...
```

To migrate to the new AST-based approach, you should:

1. Identify the code element name (function, class, etc.)
2. Replace the old format with:

```markdown

```python file=path/to/file.py element=element_name
# This will be replaced by the actual code
```

```text

## How It Works

1. **Parsing**: The tool uses AST parsing to extract code elements (functions, classes, methods) by name
2. **Markdown Processing**: It finds code references in your markdown files
3. **Code Extraction**: For each reference, it extracts the corresponding code
4. **Synchronization**: It updates the references with the current code
