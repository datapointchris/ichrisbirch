"""Tokei collector runner - captures ALL tokei output with full details."""

from __future__ import annotations

import json
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.collectors.tokei import TokeiCollectEvent
from stats.schemas.collectors.tokei import TokeiFile
from stats.schemas.collectors.tokei import TokeiFileStats
from stats.schemas.collectors.tokei import TokeiLanguageStats


def run(branch: str, project: str) -> TokeiCollectEvent:
    """Run tokei and return fully-typed event.

    Args:
        branch: Current git branch
        project: Project name

    Returns:
        TokeiCollectEvent with full language statistics
    """
    start_time = time.perf_counter()

    result = subprocess.run(  # nosec B603 B607
        ['tokei', '--output', 'json', '.'],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time

    # Parse tokei JSON output
    raw_output: dict = {}
    if result.stdout.strip():
        try:
            raw_output = json.loads(result.stdout)
        except json.JSONDecodeError:
            raw_output = {}

    languages, totals = _parse_tokei_output(raw_output)

    return TokeiCollectEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        languages=languages,
        total_code=totals['code'],
        total_comments=totals['comments'],
        total_blanks=totals['blanks'],
        total_files=totals['files'],
        duration_seconds=round(duration, 3),
    )


def _parse_tokei_output(
    raw_output: dict,
) -> tuple[dict[str, TokeiLanguageStats], dict[str, int]]:
    """Parse tokei output into structured language stats."""
    languages: dict[str, TokeiLanguageStats] = {}
    totals = {'code': 0, 'comments': 0, 'blanks': 0, 'files': 0}

    for lang_name, lang_data in raw_output.items():
        if not isinstance(lang_data, dict):
            continue

        files = [
            TokeiFile(
                name=report['name'],
                stats=TokeiFileStats(
                    blanks=report['stats']['blanks'],
                    code=report['stats']['code'],
                    comments=report['stats']['comments'],
                ),
            )
            for report in lang_data.get('reports', [])
        ]

        languages[lang_name] = TokeiLanguageStats(
            blanks=lang_data.get('blanks', 0),
            code=lang_data.get('code', 0),
            comments=lang_data.get('comments', 0),
            files=files,
            inaccurate=lang_data.get('inaccurate', False),
        )

        totals['code'] += lang_data.get('code', 0)
        totals['comments'] += lang_data.get('comments', 0)
        totals['blanks'] += lang_data.get('blanks', 0)
        totals['files'] += len(files)

    return languages, totals
