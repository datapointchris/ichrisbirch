"""npm dependencies collector runner - captures frontend package counts from package.json."""

from __future__ import annotations

import json
import time
from datetime import UTC
from datetime import datetime
from pathlib import Path

from stats.schemas.collectors.npm_dependencies import NpmDependenciesCollectEvent
from stats.schemas.collectors.npm_dependencies import NpmDependency


def run(branch: str, project: str) -> NpmDependenciesCollectEvent | None:
    """Read frontend/package.json and return dependency info.

    Args:
        branch: Current git branch
        project: Project name

    Returns:
        NpmDependenciesCollectEvent with dependency info, or None if package.json not found
    """
    start_time = time.perf_counter()

    package_json_path = Path(__file__).resolve().parent.parent.parent / 'frontend' / 'package.json'
    if not package_json_path.exists():
        return None

    with package_json_path.open() as f:
        raw_data = json.load(f)

    production_deps = _parse_dependencies(raw_data.get('dependencies', {}))
    dev_deps = _parse_dependencies(raw_data.get('devDependencies', {}))

    duration = time.perf_counter() - start_time

    return NpmDependenciesCollectEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        production_count=len(production_deps),
        dev_count=len(dev_deps),
        total_count=len(production_deps) + len(dev_deps),
        production_dependencies=production_deps,
        dev_dependencies=dev_deps,
        duration_seconds=round(duration, 3),
    )


def _parse_dependencies(deps: dict[str, str]) -> list[NpmDependency]:
    """Parse a dependencies object into NpmDependency list, stripping version prefixes."""
    return [
        NpmDependency(
            name=name,
            version=version.lstrip('^~'),
        )
        for name, version in deps.items()
    ]
