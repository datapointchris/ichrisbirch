"""Stats collection and management utilities.

DEPRECATION NOTICE:
This module (scripts/stats/) is being replaced by the event-sourced stats system
in the stats/ package. The new system provides:
- Fully typed Pydantic schemas for all events
- JSONL event streaming format
- Modular hook and collector architecture
- Discriminated union for type-safe event parsing

The legacy system here is kept for:
- Session tracking (commit journey tracking)
- S3 synchronization

New development should use the stats/ package instead:
- stats.pre_commit_capture: Capture hook outputs during pre-commit
- stats.post_commit_collect: Collect stats and emit commit events
- stats.schemas: Parse and validate events

Configuration: [tool.devstats] in pyproject.toml
"""
