"""Main script for generating all diagrams for the documentation.

This script coordinates the generation of diagrams from different sources:
1. Generating dynamic diagrams from code analysis
2. Running any custom diagram creation scripts

Run this script before building the MkDocs documentation to ensure
all diagrams are up-to-date with the current codebase.
"""

import hashlib
import json
import logging
import os
import sys
from glob import glob
from pathlib import Path

# Add project root to path to allow imports from other modules
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from tools.docs.diagram_generator.renderers.aws_diagram_renderer import generate_aws_diagrams
from tools.docs.diagram_generator.renderers.fixture_diagram_renderer import FixtureDiagramRenderer
from tools.docs.diagram_generator.renderers.testing_diagram_renderer import generate_testing_diagrams

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cache file for storing content hashes
HASH_CACHE_FILE = os.path.join(project_root, '.diagram_hash_cache.json')


def ensure_output_directory(directory):
    """Ensure the output directory exists."""
    os.makedirs(directory, exist_ok=True)
    logger.info(f'Ensured output directory exists: {directory}')


def calculate_hash_for_files(file_patterns):
    """Calculate a combined hash of the content of all files matching the patterns."""
    all_files = []
    for pattern in file_patterns:
        pattern_path = os.path.join(project_root, pattern)
        all_files.extend(glob(pattern_path, recursive=True))

    if not all_files:
        return None

    combined_hash = hashlib.md5(usedforsecurity=False)
    for file_path in sorted(all_files):
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
                combined_hash.update(file_content)
        except Exception as e:
            logger.warning(f'Failed to read file {file_path}: {e}')

    return combined_hash.hexdigest()


def has_code_changed(component, file_patterns):
    """Check if relevant code has changed by comparing hashes."""
    try:
        if not os.path.exists(HASH_CACHE_FILE):
            return True

        with open(HASH_CACHE_FILE) as f:
            cache = json.load(f)

        old_hash = cache.get(component)
        new_hash = calculate_hash_for_files(file_patterns)

        return old_hash != new_hash
    except Exception as e:
        logger.warning(f'Error checking if code changed: {e}')
        return True  # In case of error, assume code has changed


def update_hash_cache(component, file_patterns):
    """Update the hash cache for a component."""
    try:
        cache = {}
        if os.path.exists(HASH_CACHE_FILE):
            with open(HASH_CACHE_FILE) as f:
                cache = json.load(f)

        cache[component] = calculate_hash_for_files(file_patterns)

        with open(HASH_CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        logger.warning(f'Error updating hash cache: {e}')


def generate_fixture_diagrams(force=False):
    """Generate fixture diagrams based on code analysis."""
    fixture_file_patterns = [
        'tests/conftest.py',
        'tests/utils/**/*.py',
        'tools/docs/diagram_generator/renderers/fixture_diagram_renderer.py',
    ]

    if not force and not has_code_changed('fixtures', fixture_file_patterns):
        logger.info('Fixture code has not changed, skipping diagram generation')
        return

    logger.info('Generating fixture diagrams...')

    # Generate fixture diagrams
    renderer = FixtureDiagramRenderer()
    renderer.generate_all_diagrams()
    logger.info('Generated fixture diagrams')

    # Update the hash cache
    update_hash_cache('fixtures', fixture_file_patterns)


def generate_all_diagrams(force=False):
    """Generate all diagrams for documentation."""
    logger.info('Starting diagram generation process...')

    # Ensure output directory exists
    output_dir = os.path.join(project_root, 'docs', 'images', 'generated')
    ensure_output_directory(output_dir)

    # Generate fixture diagrams
    generate_fixture_diagrams(force)

    # Generate AWS diagrams (only if forced or AWS infra code has changed)
    aws_file_patterns = ['terraform/**/*']
    if force or has_code_changed('aws', aws_file_patterns):
        generate_aws_diagrams(output_dir)
        update_hash_cache('aws', aws_file_patterns)
        logger.info('Generated AWS diagrams')
    else:
        logger.info('AWS infrastructure code has not changed, skipping diagram generation')

    # Generate testing diagrams (only if forced or testing code has changed)
    testing_file_patterns = ['tests/**/*.py']
    if force or has_code_changed('testing', testing_file_patterns):
        generate_testing_diagrams(output_dir)
        update_hash_cache('testing', testing_file_patterns)
        logger.info('Generated testing diagrams')
    else:
        logger.info('Testing code has not changed, skipping diagram generation')

    logger.info('Diagram generation complete!')
    return True


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate diagrams for documentation.')
    parser.add_argument('--force', '-f', action='store_true', help='Force regeneration of all diagrams')
    args = parser.parse_args()

    success = generate_all_diagrams(force=args.force)
    sys.exit(0 if success else 1)
