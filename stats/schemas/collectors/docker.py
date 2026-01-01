"""Docker collector event schema - captures docker image/container info."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class DockerImage(BaseModel):
    """A single docker image."""

    repository: str
    tag: str
    image_id: str
    created: str
    size: str


class DockerContainer(BaseModel):
    """A single docker container."""

    container_id: str
    image: str
    command: str
    created: str
    status: str
    ports: str
    names: str


class DockerCollectEvent(BaseEvent):
    """Event for docker environment collection."""

    type: Literal['collect.docker'] = 'collect.docker'
    images: list[DockerImage]
    containers: list[DockerContainer]
    duration_seconds: float
