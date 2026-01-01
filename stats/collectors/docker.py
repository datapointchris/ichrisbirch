"""Docker collector runner - captures docker images and containers."""

from __future__ import annotations

import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.collectors.docker import DockerCollectEvent
from stats.schemas.collectors.docker import DockerContainer
from stats.schemas.collectors.docker import DockerImage


def run(branch: str, project: str) -> DockerCollectEvent:
    """Collect docker images and containers, return fully-typed event.

    Args:
        branch: Current git branch
        project: Project name

    Returns:
        DockerCollectEvent with docker environment info
    """
    start_time = time.perf_counter()

    images = _get_images()
    containers = _get_containers()

    duration = time.perf_counter() - start_time

    return DockerCollectEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        images=images,
        containers=containers,
        duration_seconds=round(duration, 3),
    )


def _get_images() -> list[DockerImage]:
    """Get list of docker images."""
    result = subprocess.run(  # nosec B603 B607
        ['docker', 'images', '--format', '{{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}\t{{.Size}}'],
        capture_output=True,
        text=True,
    )

    images = []
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) >= 5:
            images.append(
                DockerImage(
                    repository=parts[0],
                    tag=parts[1],
                    image_id=parts[2],
                    created=parts[3],
                    size=parts[4],
                )
            )
    return images


def _get_containers() -> list[DockerContainer]:
    """Get list of docker containers."""
    result = subprocess.run(  # nosec B603 B607
        ['docker', 'ps', '-a', '--format', '{{.ID}}\t{{.Image}}\t{{.Command}}\t{{.CreatedAt}}\t{{.Status}}\t{{.Ports}}\t{{.Names}}'],
        capture_output=True,
        text=True,
    )

    containers = []
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) >= 7:
            containers.append(
                DockerContainer(
                    container_id=parts[0],
                    image=parts[1],
                    command=parts[2],
                    created=parts[3],
                    status=parts[4],
                    ports=parts[5],
                    names=parts[6],
                )
            )
    return containers
