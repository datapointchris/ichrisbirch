"""Tests for docker collector schema."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime


class TestDockerSchema:
    """Tests for DockerCollectEvent schema."""

    def test_docker_image_schema(self) -> None:
        """Test DockerImage captures all fields."""
        from stats.schemas.collectors.docker import DockerImage

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
        from stats.schemas.collectors.docker import DockerCollectEvent

        event = DockerCollectEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            images=[],
            containers=[],
            duration_seconds=0.5,
        )

        assert event.type == 'collect.docker'
