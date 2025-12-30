"""Main script for generating all diagrams for the documentation.

This script coordinates the generation of diagrams from different sources:
1. Generating dynamic diagrams from code analysis
2. Running any custom diagram creation scripts

Run this script as a module from the project root:
    python -m tools.docs.diagram_generator.generate_diagrams

Or use the pre-commit hook which handles the import path correctly.
"""

import argparse
import hashlib
import json
import logging
import sys
from glob import glob
from pathlib import Path

from ..utils import find_project_root
from .renderers.aws_diagram_renderer import generate_aws_diagrams
from .renderers.fixture_diagram_renderer import FixtureDiagramRenderer
from .renderers.testing_diagram_renderer import generate_testing_diagrams

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get project root using utility function
PROJECT_ROOT = find_project_root()
HASH_CACHE_FILE = PROJECT_ROOT / '.diagram_hash_cache.json'


def ensure_output_directory(directory: Path) -> None:
    """Ensure the output directory exists."""
    directory.mkdir(parents=True, exist_ok=True)
    logger.info(f'Ensured output directory exists: {directory}')


def calculate_hash_for_files(file_patterns: list[str]) -> str | None:
    """Calculate a combined hash of the content of all files matching the patterns."""
    all_files = []
    for pattern in file_patterns:
        pattern_path = PROJECT_ROOT / pattern
        all_files.extend(glob(str(pattern_path), recursive=True))

    if not all_files:
        return None

    combined_hash = hashlib.md5(usedforsecurity=False)
    for file_path in sorted(all_files):
        try:
            file_content = Path(file_path).read_bytes()
            combined_hash.update(file_content)
        except Exception as e:
            logger.warning(f'Failed to read file {file_path}: {e}')

    return combined_hash.hexdigest()


def has_code_changed(component: str, file_patterns: list[str]) -> bool:
    """Check if relevant code has changed by comparing hashes."""
    try:
        if not HASH_CACHE_FILE.exists():
            return True

        cache = json.loads(HASH_CACHE_FILE.read_text())
        old_hash = cache.get(component)
        new_hash = calculate_hash_for_files(file_patterns)

        return old_hash != new_hash
    except Exception as e:
        logger.warning(f'Error checking if code changed: {e}')
        return True


def update_hash_cache(component: str, file_patterns: list[str]) -> None:
    """Update the hash cache for a component."""
    try:
        cache = {}
        if HASH_CACHE_FILE.exists():
            cache = json.loads(HASH_CACHE_FILE.read_text())

        cache[component] = calculate_hash_for_files(file_patterns)
        HASH_CACHE_FILE.write_text(json.dumps(cache, indent=2))
    except Exception as e:
        logger.warning(f'Error updating hash cache: {e}')


def generate_fixture_diagrams(force: bool = False) -> None:
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
    renderer = FixtureDiagramRenderer()
    renderer.generate_all_diagrams()
    logger.info('Generated fixture diagrams')
    update_hash_cache('fixtures', fixture_file_patterns)


def generate_all_diagrams(force: bool = False) -> bool:
    """Generate all diagrams for documentation."""
    logger.info('Starting diagram generation process...')

    output_dir = PROJECT_ROOT / 'docs' / 'images' / 'generated'
    ensure_output_directory(output_dir)

    generate_fixture_diagrams(force)

    aws_file_patterns = ['terraform/**/*']
    if force or has_code_changed('aws', aws_file_patterns):
        generate_aws_diagrams(str(output_dir))
        update_hash_cache('aws', aws_file_patterns)
        logger.info('Generated AWS diagrams')
    else:
        logger.info('AWS infrastructure code has not changed, skipping diagram generation')

    testing_file_patterns = ['tests/**/*.py']
    if force or has_code_changed('testing', testing_file_patterns):
        generate_testing_diagrams(str(output_dir))
        update_hash_cache('testing', testing_file_patterns)
        logger.info('Generated testing diagrams')
    else:
        logger.info('Testing code has not changed, skipping diagram generation')

    logger.info('Diagram generation complete!')
    return True


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Generate diagrams for documentation.')
    parser.add_argument('--force', '-f', action='store_true', help='Force regeneration of all diagrams')
    args = parser.parse_args()

    success = generate_all_diagrams(force=args.force)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
