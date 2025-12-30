#!/usr/bin/env python
"""Verification script to test that the diagram generator works correctly after the reorganization. This script:

1. Imports and runs the diagram generation process
2. Verifies that all expected output files are created
3. Reports success or any issues encountered
"""

import logging
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('verify_diagram_generator')


def verify_diagram_generator():
    """Test that the diagram generator works correctly with the new directory structure."""
    logger.info('Starting verification of diagram generator...')

    try:
        # Import the diagram generator
        from tools.docs.diagram_generator.generate_diagrams import generate_all_diagrams

        # Run the generator
        logger.info('Running diagram generator...')
        result = generate_all_diagrams()

        if not result:
            logger.error('Diagram generator reported failure')
            return False

        # Check that output files were created
        output_dir = project_root / 'docs' / 'images' / 'generated'
        expected_files = [
            'fixtures_diagram.svg',
            'fixture_scopes.svg',
            'fixture_dependencies.svg',
            'fixture_dependencies_session.svg',
            'fixture_dependencies_module.svg',
            'fixture_dependencies_function.svg',
            'fixtures_comprehensive.svg',
            'aws_iam.svg',
            'test_env_architecture.svg',
            'test_env_setup_sequence.svg',
            'test_env_teardown_sequence.svg',
            'test_writing_workflow.svg',
        ]

        # Count how many files exist
        missing_files = []
        for file_name in expected_files:
            file_path = output_dir / file_name
            if not file_path.exists():
                missing_files.append(file_name)

        if missing_files:
            logger.error(f'Missing {len(missing_files)} expected output files:')
            for file_name in missing_files:
                logger.error(f'  - {file_name}')
            return False

        logger.info(f'Successfully verified all {len(expected_files)} expected diagram files were created!')
        return True

    except Exception as e:
        logger.exception(f'Error during verification: {str(e)}')
        return False


if __name__ == '__main__':
    success = verify_diagram_generator()
    sys.exit(0 if success else 1)
