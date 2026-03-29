"""CLI for the seed system."""

from __future__ import annotations

import argparse
import os


def main():
    parser = argparse.ArgumentParser(
        description='Seed database with curated, realistic development data',
    )
    parser.add_argument('--scale', type=int, default=1, help='Scale multiplier for record counts (default: 1)')
    parser.add_argument(
        '--env',
        type=str,
        choices=['development', 'testing'],
        default='development',
        help='Target environment (default: development)',
    )
    parser.add_argument('--dry-run', action='store_true', help='List what would be seeded without inserting')
    parser.add_argument('--only', type=str, default=None, help='Comma-separated seeder names (e.g. tasks,books)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility (default: 42)')

    args = parser.parse_args()

    os.environ['ENVIRONMENT'] = args.env

    from ichrisbirch.config import get_settings
    from scripts.seed.run import run_seed

    settings = get_settings()
    only = args.only.split(',') if args.only else None

    run_seed(
        settings=settings,
        scale=args.scale,
        dry_run=args.dry_run,
        only=only,
        faker_seed=args.seed,
    )
