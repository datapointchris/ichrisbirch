# Dynamic Documentation System

This directory contains tools for maintaining dynamic, always up-to-date documentation through:

1. **Automatically generated diagrams** based on code structure
2. **Code synchronization** to keep documentation examples aligned with the codebase
3. **MkDocs integration** for seamless incorporation into your documentation

## System Components

```text
docs/diagram_generator/
├── README.md                     # This file
├── generate_diagrams.py          # Main script to generate all diagrams
├── mkdocs_code_sync_plugin.py    # Plugin to sync code snippets
├── mkdocs_diagrams_plugin.py     # Plugin to generate diagrams during builds
├── analyzers/                    # Code structure analyzers
│   └── fixture_analyzer.py       # Analyzes test fixtures
├── converters/                   # Format conversion tools
│   └── mermaid_to_graphviz.py    # Converts Mermaid to Graphviz
└── renderers/                    # Diagram renderers
    └── fixture_diagram_renderer.py  # Renders fixture diagrams
```

## How to Use

### Building Documentation with Updated Diagrams

Simply run the MkDocs build command:

```bash
mkdocs build
```

or for development server:

```bash
mkdocs serve
```

The plugins will automatically:

### Using Code Synchronization

To include synchronized code snippets in your Markdown files, use code blocks with special attributes:

````markdown

```python file=path/to/file.py lines=10-20 label="Example from source file"

# This content will be replaced with the actual code from the file

```
````

Available attributes:

- **file**: Path to the source file (relative to project root)
- **lines**: Optional line range (e.g., `10-20`)
- **highlight_lines**: Comma-separated list of lines to highlight (e.g., `1,3,5-10`)
- **indent**: Number of spaces to indent each line (useful for nested examples)
- **trim**: `true` or `false` - Remove leading/trailing blank lines (default: `true`)

### 1. Create an Analyzer

Create a new Python module in the `analyzers/` directory that analyzes your code structure:

```python
# docs/diagram_generator/analyzers/my_analyzer.py
def analyze_my_component():
    return analysis_data
```

### 2. Create a Renderer

Create a new Python module in the `renderers/` directory that renders diagrams from analyzed data:

```python
# docs/diagram_generator/renderers/my_renderer.py
from graphviz import Digraph
from docs.diagram_generator.analyzers.my_analyzer import analyze_my_component

class MyDiagramRenderer:
    """Renders diagrams for my component."""

    def __init__(self, analysis_data=None):
        self.analysis_data = analysis_data or analyze_my_component()

    def render_diagram(self, output_path='docs/images/generated/my_diagram'):
        """Render a diagram using Graphviz."""
        dot = Digraph(comment='My Component Diagram')
        # Create your diagram using dot
        dot.render(output_path, format='svg', cleanup=True)
        return dot
```

### 3. Update the Main Generator

Modify `generate_diagrams.py` to include your new diagram renderer:

```python
# In generate_diagrams.py, add to the generate_dynamic_diagrams function:

from docs.diagram_generator.renderers.my_renderer import MyDiagramRenderer

def generate_dynamic_diagrams():
    # Existing code...

    # Add your renderer
    my_renderer = MyDiagramRenderer()
    my_renderer.render_diagram()
    logger.info("Generated my component diagrams")
```

## Integration with MkDocs Material

This system is designed to work seamlessly with MkDocs Material. Configuration is in your project's `mkdocs.yml`:

```yaml
plugins:
  - search
  # Other plugins...
  - diagrams:
      module: docs.diagram_generator.mkdocs_diagrams_plugin
      class: DiagramGeneratorPlugin
      config:
        generate_diagrams: true
  - code_sync:
      module: docs.diagram_generator.mkdocs_code_sync_plugin
      class: CodeSyncPlugin
      config:
        sync_code: true
        base_path: ''  # Project root
```

## Dependencies

- **Graphviz**: For diagram rendering (`pip install graphviz`)
- **MkDocs**: Documentation framework
- **MkDocs Material**: Theme and extensions
- **Python 3.6+**: For AST parsing and other features

## Best Practices

1. **Keep diagrams focused**: Each diagram should visualize one specific aspect
2. **Use consistent styling**: Maintain visual consistency across diagrams
3. **Document diagram meanings**: Include legend or explanation text with complex diagrams
4. **Generate only what's needed**: Add conditions to skip unnecessary diagrams
5. **Leverage code comments**: Use docstrings and comments as sources for diagram content
6. **Separate layout from content**: Separate the structure analysis from visual presentation
7. **Use incremental rendering**: Update only what changed if performance becomes an issue

## Troubleshooting

### Diagrams Not Updating

1. Ensure Graphviz is installed and available in your PATH
2. Verify the output directory (`docs/images/generated/`) is writa
ble
3. Check logs for errors during diagram generation
4. Run the generator manually to see detailed error messages

### Code Synchronization Issues

1. Verify file paths are correct (relative to project root)

2. Check that the specified line ranges exist in the source files
3. Escape any special characters in markup as needed

### MkDocs Build Errors

1. Ensure all plugin dependencies are installed
2. Check that plugin paths in `mkdocs.yml` are correct
3. Try running with more verbose logging: `mkdocs build --verbose`
