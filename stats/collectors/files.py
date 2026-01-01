"""Files collector runner - captures file statistics."""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import UTC
from datetime import datetime
from pathlib import Path

from stats.schemas.collectors.files import FilesCollectEvent
from stats.schemas.collectors.files import FileTypeStats


def run(branch: str, project: str, root_path: str = '.') -> FilesCollectEvent:
    """Collect file statistics, return fully-typed event.

    Args:
        branch: Current git branch
        project: Project name
        root_path: Root directory to scan

    Returns:
        FilesCollectEvent with file statistics
    """
    start_time = time.perf_counter()

    stats_by_ext: dict[str, dict[str, int]] = defaultdict(lambda: {'count': 0, 'size': 0})
    total_files = 0
    total_size = 0

    root = Path(root_path)
    for path in root.rglob('*'):
        if path.is_file() and not _should_skip(path):
            ext = path.suffix or '(no extension)'
            try:
                size = path.stat().st_size
                stats_by_ext[ext]['count'] += 1
                stats_by_ext[ext]['size'] += size
                total_files += 1
                total_size += size
            except OSError:
                continue

    duration = time.perf_counter() - start_time

    file_types = [
        FileTypeStats(
            extension=ext,
            count=data['count'],
            total_size_bytes=data['size'],
        )
        for ext, data in sorted(stats_by_ext.items(), key=lambda x: x[1]['count'], reverse=True)
    ]

    return FilesCollectEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        file_types=file_types,
        total_files=total_files,
        total_size_bytes=total_size,
        duration_seconds=round(duration, 3),
    )


def _should_skip(path: Path) -> bool:
    """Check if a path should be skipped."""
    skip_dirs = {'.git', '.venv', 'node_modules', '__pycache__', '.pytest_cache', '.mypy_cache'}
    return any(part in skip_dirs for part in path.parts)
