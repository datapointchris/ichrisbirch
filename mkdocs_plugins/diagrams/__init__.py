"""MkDocs plugin for generating diagrams dynamically during documentation build.

This plugin hooks into the MkDocs build process to ensure all diagrams are up-to-date before the documentation is built.
"""

import logging
import time

from mkdocs.config.config_options import Type
from mkdocs.plugins import BasePlugin

from .generate import generate_all_diagrams

__all__ = ['DiagramGeneratorPlugin', 'generate_all_diagrams']


class DiagramGeneratorPlugin(BasePlugin):
    """MkDocs plugin that generates diagrams before building documentation."""

    config_scheme = (('generate_diagrams', Type(bool, default=True)),)

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.enabled = True
        self.is_serve_mode = False
        self.last_generation_time = 0
        self.min_generation_interval = 3600  # 1 hour

    def on_config(self, config):
        """Called when the config is loaded."""
        self.enabled = self.config.get('generate_diagrams', True)

        if hasattr(config, 'watch') and config.watch:
            self.is_serve_mode = True
            self.logger.info('Running in MkDocs serve mode - diagram generation will be limited.')

        return config

    def on_pre_build(self, config):
        """Called before the build starts."""
        current_time = time.time()

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
            self.logger.warning('Continuing with build despite diagram generation error.')
