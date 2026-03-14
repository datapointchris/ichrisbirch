"""CLI for the seed system."""

from __future__ import annotations

import argparse
import os


def main():
    parser = argparse.ArgumentParser(
        description='Seed database with auto-discovered, combinatorially-correct data',
    )
    parser.add_argument('--scale', type=int, default=1, help='Scale multiplier for record counts (default: 1)')
    parser.add_argument('--config', type=str, default=None, help='Path to TOML config (default: scripts/seed/seed_config.toml)')
    parser.add_argument(
        '--env',
        type=str,
        choices=['development', 'testing'],
        default='development',
        help='Target environment (default: development)',
    )
    parser.add_argument('--dry-run', action='store_true', help='Discover and generate without inserting')
    parser.add_argument('--only', nargs='+', metavar='MODEL', help='Seed only these model names')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--seed', type=int, default=42, help='Faker random seed (default: 42)')

    args = parser.parse_args()

    os.environ['ENVIRONMENT'] = args.env

    from pathlib import Path

    from ichrisbirch.config import get_settings
    from scripts.seed.seeder import run_seed

    settings = get_settings()
    config_path = Path(args.config) if args.config else Path(__file__).parent / 'seed_config.toml'

    run_seed(
        settings=settings,
        scale=args.scale,
        config_path=config_path,
        dry_run=args.dry_run,
        only=args.only,
        faker_seed=args.seed,
        verbose=args.verbose,
    )
