"""MkDocs plugin for generating diagrams dynamically during documentation build.

This plugin hooks into the MkDocs build process to ensure all diagrams are up-to-date before the documentation is built.
"""

import logging
import os
import sys
import time
from pathlib import Path

from mkdocs.config.config_options import Type
from mkdocs.plugins import BasePlugin

# Set up path for importing the diagram generator
current_file_path = Path(__file__)
project_root = current_file_path.parent.parent.parent.parent
sys.path.append(str(project_root))

# Import the diagram generator now, at module level
from tools.docs.diagram_generator.generate_diagrams import generate_all_diagrams  # noqa: E402


class DiagramGeneratorPlugin(BasePlugin):
    """MkDocs plugin that generates diagrams before building documentation."""

    config_scheme = (('generate_diagrams', Type(bool, default=True)),)

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.enabled = True
        self.is_serve_mode = False
        self.last_generation_time = 0
        # Minimum time (in seconds) between diagram regenerations in serve mode
        self.min_generation_interval = 3600  # 1 hour

    def on_config(self, config):
        """Called when the config is loaded."""
        self.enabled = self.config.get('generate_diagrams', True)

        # Detect if we're running in serve mode
        if hasattr(config, 'watch') and config.watch:
            self.is_serve_mode = True
            self.logger.info('Running in MkDocs serve mode - diagram generation will be limited.')

        return config

    def on_pre_build(self, config):
        """Called before the build starts."""
        current_time = time.time()

        # Skip diagram generation if:
        # 1. Plugin is disabled
        # 2. We're in serve mode and it's been less than the minimum interval
        if not self.enabled:
            self.logger.info('Diagram generation is disabled. Skipping.')
            return

        if self.is_serve_mode:
            time_since_last_generation = current_time - self.last_generation_time
            if time_since_last_generation < self.min_generation_interval:
                self.logger.info(
                    f'Skipping diagram generation in serve mode (last generated {time_since_last_generation:.1f}s ago). '
                    f'Use pre-commit hook or manual generation instead.'
                )
                return

        self.logger.info('Running diagram generation before building docs...')
        try:
            generate_all_diagrams()
            self.last_generation_time = current_time
            self.logger.info('Diagram generation completed successfully!')
        except Exception as e:
            self.logger.error(f'Error generating diagrams: {e}')
            # Don't fail the build if diagram generation fails
            self.logger.warning('Continuing with build despite diagram generation error.')


# Entry point for the MkDocs plugin
entry_point = DiagramGeneratorPlugin
