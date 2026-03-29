"""Orchestrator: calls each seeder in dependency order."""

from __future__ import annotations

import random

import structlog
from faker import Faker

from ichrisbirch.config import Settings
from ichrisbirch.database.session import create_session
from scripts.seed.base import SeedResult
from scripts.seed.seeders import SEED_ORDER

logger = structlog.get_logger()


def run_seed(
    settings: Settings,
    scale: int = 1,
    dry_run: bool = False,
    only: list[str] | None = None,
    faker_seed: int = 42,
) -> list[SeedResult]:
    """Main entry point: clear old data, seed each entity in order, commit."""
    Faker.seed(faker_seed)
    random.seed(faker_seed)

    seeders = SEED_ORDER.copy()
    if only:
        seeders = [(name, mod) for name, mod in seeders if name in only]

    logger.info('seed_starting', scale=scale, dry_run=dry_run, seeders=[n for n, _ in seeders])

    if dry_run:
        for name, _ in seeders:
            logger.info('dry_run', seeder=name)
        return []

    with create_session(settings) as session:
        # Clear in reverse order (children first)
        for _name, mod in reversed(seeders):
            mod.clear(session)
        session.flush()

        results = []
        for _name, mod in seeders:
            result = mod.seed(session, scale)
            results.append(result)
            logger.info('seeded', model=result.model, count=result.count, details=result.details)

        session.commit()
        total = sum(r.count for r in results)
        logger.info('seed_complete', total=total)

    return results
