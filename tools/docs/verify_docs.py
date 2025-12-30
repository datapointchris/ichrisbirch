#!/usr/bin/env python3
"""Verification script for documentation generation.

This script helps verify that the documentation is being generated correctly:
1. It checks for the presence of generated diagrams.
2. It verifies that code snippets have been synchronized.
3. It ensures the MkDocs build completes without errors.
"""

import argparse
import logging
import subprocess  # nosec
import sys

from .utils import find_project_root

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('docs_verification.log')],
)
logger = logging.getLogger('docs_verification')

# Define project paths
PROJECT_ROOT = find_project_root()


def run_command(command, cwd=None):
    """Run a shell command and return the output."""
    logger.info(f'Running command: {command}')
    result = subprocess.run(command, shell=True, cwd=cwd or PROJECT_ROOT, capture_output=True, text=True)  # nosec

    if result.returncode != 0:
        logger.error(f'Command failed with code {result.returncode}')
        logger.error(f'Error output: {result.stderr}')
        return False, result.stderr

    return True, result.stdout


def check_generated_diagrams():
    """Check for the presence of generated diagrams."""
    logger.info('Checking for generated diagrams...')

    generated_diagrams_dir = PROJECT_ROOT / 'docs' / 'images' / 'generated'
    if not generated_diagrams_dir.exists():
        logger.error(f'Generated diagrams directory not found: {generated_diagrams_dir}')
        return False

    diagrams = list(generated_diagrams_dir.glob('*.svg'))
    if not diagrams:
        logger.error('No SVG diagrams found in the generated diagrams directory')
        return False

    logger.info(f'Found {len(diagrams)} generated diagrams')
    for diagram in diagrams[:5]:  # List the first 5 diagrams
        logger.info(f'- {diagram.name}')

    if len(diagrams) > 5:
        logger.info(f'... and {len(diagrams) - 5} more')

    return True


def check_code_sync():
    """Check if code snippets have been synchronized in the documentation."""
    logger.info('Checking for synchronized code snippets...')

    # Get a list of markdown files
    docs_dir = PROJECT_ROOT / 'docs'
    markdown_files = list(docs_dir.glob('**/*.md'))

    if not markdown_files:
        logger.error('No markdown files found in docs directory')
        return False

    # Sample check: look for file= attributes in code blocks
    code_blocks_with_file_attr = 0

    for file_path in markdown_files:
        try:
            content = file_path.read_text(encoding='utf-8')
            if '```' in content and 'file=' in content:
                code_blocks_with_file_attr += 1
        except Exception as e:
            logger.error(f'Error reading {file_path}: {e}')

    if code_blocks_with_file_attr == 0:
        logger.warning('No code blocks with file= attribute found. Code sync may not be working.')
        return False

    logger.info(f'Found {code_blocks_with_file_attr} markdown files with code blocks that use file= attribute')
    return True


def verify_mkdocs_build():
    """Verify that MkDocs build completes without errors."""
    logger.info('Verifying MkDocs build...')

    # Run MkDocs build
    success, output = run_command('mkdocs build --clean')
    if not success:
        return False

    # Check if site directory was created
    site_dir = PROJECT_ROOT / 'site'
    if not site_dir.exists() or not site_dir.is_dir():
        logger.error('MkDocs site directory not found after build')
        return False

    # Check if index.html exists
    index_html = site_dir / 'index.html'
    if not index_html.exists():
        logger.error('index.html not found in site directory')
        return False

    logger.info('MkDocs build completed successfully')
    return True


def main():
    parser = argparse.ArgumentParser(description='Verify documentation generation')
    parser.add_argument('--diagrams-only', action='store_true', help='Only check generated diagrams')
    parser.add_argument('--code-sync-only', action='store_true', help='Only check code sync')
    parser.add_argument('--build-only', action='store_true', help='Only verify MkDocs build')
    args = parser.parse_args()

    results = {}

    # Run selected checks or all checks if none specified
    if args.diagrams_only:
        results['diagrams'] = check_generated_diagrams()
    elif args.code_sync_only:
        results['code_sync'] = check_code_sync()
    elif args.build_only:
        results['build'] = verify_mkdocs_build()
    else:
        results['diagrams'] = check_generated_diagrams()
        results['code_sync'] = check_code_sync()
        results['build'] = verify_mkdocs_build()

    # Summarize results
    logger.info('\n--- Results Summary ---')
    all_passed = True
    for check, passed in results.items():
        status = 'PASSED' if passed else 'FAILED'
        logger.info(f'{check.upper()}: {status}')
        all_passed = all_passed and passed

    if all_passed:
        logger.info('All checks passed! Documentation generation is working correctly.')
        return 0
    else:
        logger.error('Some checks failed. Review the logs for details.')
        return 1


if __name__ == '__main__':
    sys.exit(main())
