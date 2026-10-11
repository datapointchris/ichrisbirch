"""Tests for docker collector schema."""

from __future__ import annotations

import datetime as dt

from stats.schemas.collectors.docker import DockerCollectEvent
from stats.schemas.collectors.docker import DockerImage


class TestDockerSchema:
    """Tests for DockerCollectEvent schema."""

    def test_docker_image_schema(self) -> None:
        """Test DockerImage captures all fields."""
        image = DockerImage(
            repository='python',
            tag='3.13',
            image_id='abc123',
            created='2025-01-01',
            size='1GB',
        )

        assert image.repository == 'python'
        assert image.tag == '3.13'

    def test_docker_collect_event_schema(self) -> None:
        """Test DockerCollectEvent schema."""
        event = DockerCollectEvent(
            timestamp=dt.datetime.now(dt.UTC),
            project='ichrisbirch',
            branch='master',
            images=[],
            containers=[],
            duration_seconds=0.5,
        )

        assert event.type == 'collect.docker'
