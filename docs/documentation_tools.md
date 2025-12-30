# Documentation Tools

This project includes tools for generating and maintaining documentation that stays in sync with the codebase.

## Code Sync Tool

The code sync tool (`tools/code_sync/`) automatically synchronizes code snippets in documentation with actual source code. This ensures documentation examples are always up-to-date.

### Features

- **AST-based extraction**: References Python functions, classes, and methods by name (survives refactoring)
- **Line-based extraction**: References any file type by line numbers (for configs, shell scripts, etc.)
- **Decorator support**: Automatically includes decorators when extracting functions/classes
- **MkDocs integration**: Plugin syncs code during `mkdocs serve` and `mkdocs build`
- **Pre-commit hook**: Syncs code before each commit
- **CI verification**: GitHub Action fails if docs are out of sync

### Markdown Syntax

#### AST-Based References (Recommended for Python)

Reference Python functions, classes, or methods by name. Use this format in your markdown:

    ```python file=path/to/file.py element=function_name
    # This content is auto-replaced with the actual function code
    ```

For example, to reference a function called `my_function` from `src/utils.py`:

    ```python file=src/utils.py element=my_function
    ```

To reference a class method:

    ```python file=src/models.py element=MyClass.my_method
    ```

To reference an entire class:

    ```python file=src/models.py element=MyClass
    ```

#### Line-Based References (For Non-Python Files)

Reference specific line ranges from any file:

    ```bash file=scripts/deploy.sh lines=10-25
    # This content is auto-replaced with lines 10-25 from the file
    ```

Examples:

    ```yaml file=config/settings.yml lines=1-20
    ```

    ```dockerfile file=Dockerfile lines=100-120
    ```

#### Optional Attributes

Add a label/title to the code block:

    ```python file=src/utils.py element=my_function label="My Utility Function"
    ```

### CLI Usage

The tool can be run directly from the command line:

```bash
# Sync all docs with source code
python -m tools.code_sync docs --base-path .

# Check if docs are in sync (CI mode - exits 1 if out of sync)
python -m tools.code_sync docs --base-path . --check

# Verbose output
python -m tools.code_sync docs --base-path . -v
```

### How It Works

1. Scans markdown files for code blocks with `file=` and `element=` or `lines=` attributes
2. For AST-based references:
   - Parses the Python file using Python's `ast` module
   - Finds the named element (function, class, method)
   - Extracts the complete code including decorators and docstrings
3. For line-based references:
   - Reads the specified line range from the file
4. Replaces the code block content with the extracted code
5. Writes the updated markdown file

### Automation

#### Pre-commit Hook

The pre-commit hook runs automatically before each commit:

```yaml
# In .pre-commit-config.yaml
- id: code-sync
  name: Code Sync
  entry: python -m tools.code_sync
  args: ["docs", "--base-path", "."]
```

#### MkDocs Plugin

The MkDocs plugin syncs code during documentation builds:

```yaml
# In mkdocs.yml
plugins:
  - code_sync:
      enabled: true
```

#### GitHub Actions

The CI workflow verifies docs are in sync:

```yaml
# In .github/workflows/sync-docs-code.yml
- name: Run Code Sync Check
  run: python -m tools.code_sync docs --base-path . --check
```

### Best Practices

1. **Prefer AST-based references** for Python code - they survive refactoring
2. **Use line-based references** only for non-Python files or when you need a specific section
3. **Keep referenced elements focused** - reference specific functions rather than entire modules
4. **Run locally before pushing** - use `python -m tools.code_sync docs --base-path . --check` to verify
5. **Use meaningful labels** - helps readers understand what the code shows

---

## Diagram Generator

The diagram generator (`tools/docs/diagram_generator/`) creates visual diagrams from code analysis.

### Directory Structure

```text
tools/docs/diagram_generator/
├── analyzers/           # Code that analyzes project structure
│   └── fixture_analyzer.py
├── renderers/           # Code that renders diagrams
│   ├── aws_diagram_renderer.py
│   ├── fixture_diagram_renderer.py
│   └── testing_diagram_renderer.py
└── generate_diagrams.py # Main generation script
```

### Usage

Generate all diagrams:

```bash
python -m tools.docs.diagram_generator.generate_diagrams

# Force regeneration (ignore cache)
python -m tools.docs.diagram_generator.generate_diagrams --force
```

Generated diagrams are saved to `docs/images/generated/`.

### MkDocs Integration

The diagrams plugin regenerates diagrams during builds:

```yaml
# In mkdocs.yml
plugins:
  - diagrams:
      generate_diagrams: true
```

### Caching

The generator caches content hashes to avoid unnecessary regeneration. The cache is stored in `.diagram_hash_cache.json` at the project root.

### Adding New Diagrams

1. Create a new renderer in `tools/docs/diagram_generator/renderers/`
2. Add the renderer call to `generate_diagrams.py`
3. Reference the generated diagram in your documentation using standard markdown image syntax
