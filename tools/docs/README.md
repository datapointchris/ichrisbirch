# Documentation Tools

This directory contains tools and utilities for generating and maintaining the project's documentation.

## Directory Structure

- `diagram_generator/`: Tools for generating diagrams used in documentation
  - `analyzers/`: Code that analyzes the project structure to generate diagram data
  - `renderers/`: Code that renders diagrams from analyzed data
  - `generate_diagrams.py`: Main script to generate all diagrams
  - `mkdocs_diagrams_plugin.py`: MkDocs plugin to generate diagrams during site build
  - `mkdocs_code_sync_plugin.py`: MkDocs plugin to sync code examples with actual code

## Usage

### Generate Diagrams

To generate all diagrams for the documentation, run:

```bash
python -m tools.docs.diagram_generator.generate_diagrams
```

This will:

infrastructure
ing architecture

All generated diagrams are saved in the `docs/images/generated/` directory.

### MkDocs Integration

The diagram generator is integrated with MkDocs via plugins defined in `mkdocs.yml`. When building the documentation site, these plugins:

1. Automatically regenerate diagrams before building the site
2. Synchronize code examples with actual project code

## Development

When adding new types of diagrams:

1. Create a new renderer in the `diagram_generator/renderers/` directory
2. Add the renderer to `generate_diagrams.py`

3. Update the documentation to reference the new diagrams
