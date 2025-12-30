"""MkDocs plugin for generating diagrams dynamically during documentation build.

This plugin hooks into the MkDocs build process to ensure all diagrams are up-to-date before the documentation is built.
"""

import logging
from pathlib import Path

from mkdocs.config.config_options import Type
from mkdocs.plugins import BasePlugin

# Import the diagram generation script
project_root = Path(__file__).parent.parent.parent.parent
import sys

sys.path.append(str(project_root))
from tools.docs.diagram_generator.generate_diagrams import generate_all_diagrams


class DiagramGeneratorPlugin(BasePlugin):
    """MkDocs plugin that generates diagrams before building documentation."""

    config_scheme = (('generate_diagrams', Type(bool, default=True)),)

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.enabled = True

    def on_config(self, config):
        """Called when the config is loaded."""
        self.enabled = self.config.get('generate_diagrams', True)
        return config

    def on_pre_build(self, config):
        """Called before the build starts."""
        if self.enabled:
            self.logger.info('Running diagram generation before building docs...')
            try:
                generate_all_diagrams()
                self.logger.info('Diagram generation completed successfully!')
            except Exception as e:
                self.logger.error(f'Error generating diagrams: {e}')
                # Don't fail the build if diagram generation fails
                self.logger.warning('Continuing with build despite diagram generation error.')
        else:
            self.logger.info('Diagram generation is disabled. Skipping.')
