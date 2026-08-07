"""Files collector runner - captures file statistics."""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import UTC
from datetime import datetime

from stats.collectors.walk import iter_files
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

    for path in iter_files(root_path):
        ext = path.suffix or '(no extension)'
        try:
            size = path.stat().st_size
        except OSError:  # a broken symlink is a name, not a file
            continue
        stats_by_ext[ext]['count'] += 1
        stats_by_ext[ext]['size'] += size
        total_files += 1
        total_size += size

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
