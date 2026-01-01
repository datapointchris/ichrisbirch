"""Radon collector runner - captures code complexity metrics."""

from __future__ import annotations

import json
import subprocess  # nosec B404
import time
from contextlib import suppress
from datetime import UTC
from datetime import datetime
from pathlib import Path

from stats.schemas.collectors.radon import FileComplexity
from stats.schemas.collectors.radon import FunctionComplexity
from stats.schemas.collectors.radon import RadonCollectEvent


def run(branch: str, project: str, root_path: str = '.') -> RadonCollectEvent | None:
    """Collect code complexity metrics using radon.

    Args:
        branch: Current git branch
        project: Project name
        root_path: Root path to analyze (default: current directory)

    Returns:
        RadonCollectEvent with complexity metrics, or None if radon fails
    """
    start_time = time.perf_counter()

    # Find Python files to analyze
    all_py_files = list(Path(root_path).rglob('*.py'))
    python_files = [str(f) for f in all_py_files if '.venv' not in str(f) and '__pycache__' not in str(f) and 'alembic' not in str(f)]

    if not python_files:
        return None

    # Get cyclomatic complexity
    cc_result = subprocess.run(  # nosec B603 B607
        ['uv', 'run', 'radon', 'cc', '-j', *python_files],
        capture_output=True,
        text=True,
    )

    cc_data: dict = {}
    if cc_result.returncode == 0 and cc_result.stdout:
        with suppress(json.JSONDecodeError):
            cc_data = json.loads(cc_result.stdout)

    # Get maintainability index
    mi_result = subprocess.run(  # nosec B603 B607
        ['uv', 'run', 'radon', 'mi', '-j', *python_files],
        capture_output=True,
        text=True,
    )

    mi_data: dict = {}
    if mi_result.returncode == 0 and mi_result.stdout:
        with suppress(json.JSONDecodeError):
            mi_data = json.loads(mi_result.stdout)

    # Combine into file complexity records
    files: list[FileComplexity] = []
    total_complexity = 0
    total_mi = 0.0

    for filepath in python_files:
        cc_funcs = cc_data.get(filepath, [])
        mi_info = mi_data.get(filepath, {})

        if not cc_funcs and not mi_info:
            continue

        functions = [
            FunctionComplexity(
                name=f.get('name', ''),
                complexity=f.get('complexity', 0),
                rank=f.get('rank', 'A'),
                lineno=f.get('lineno', 0),
            )
            for f in cc_funcs[:10]  # Top 10 functions per file
        ]

        complexities = [f.get('complexity', 0) for f in cc_funcs]
        file_total = sum(complexities)
        file_avg = round(file_total / len(complexities), 2) if complexities else 0
        file_max = max(complexities) if complexities else 0

        mi_value = mi_info.get('mi', 100.0) if isinstance(mi_info, dict) else 100.0
        mi_rank = mi_info.get('rank', 'A') if isinstance(mi_info, dict) else 'A'

        files.append(
            FileComplexity(
                path=filepath,
                function_count=len(cc_funcs),
                total_complexity=file_total,
                avg_complexity=file_avg,
                max_complexity=file_max,
                maintainability_index=round(mi_value, 2),
                maintainability_rank=mi_rank,
                functions=functions,
            )
        )

        total_complexity += file_total
        total_mi += mi_value

    duration = time.perf_counter() - start_time

    avg_complexity = round(total_complexity / len(files), 2) if files else 0
    avg_maintainability = round(total_mi / len(files), 2) if files else 0

    return RadonCollectEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        files=files,
        total_files=len(files),
        avg_complexity=avg_complexity,
        avg_maintainability=avg_maintainability,
        duration_seconds=round(duration, 3),
    )
