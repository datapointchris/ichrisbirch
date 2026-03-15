from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict


class AdminConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DockerContainerStatus(AdminConfig):
    name: str
    status: str
    started_at: str | None = None
    image: str


class TableRowCount(AdminConfig):
    schema_name: str
    table_name: str
    row_count: int


class DatabaseStats(AdminConfig):
    tables: list[TableRowCount]
    total_size_mb: float
    active_connections: int


class RedisStats(AdminConfig):
    key_count: int
    memory_used_human: str
    connected_clients: int
    uptime_seconds: int


class DiskUsage(AdminConfig):
    total_gb: float
    used_gb: float
    free_gb: float
    percent_used: float


class ServerInfo(AdminConfig):
    environment: str
    api_url: str
    server_time: str


class SystemHealth(AdminConfig):
    server: ServerInfo
    docker: list[DockerContainerStatus]
    database: DatabaseStats
    redis: RedisStats
    disk: DiskUsage


class RecentError(AdminConfig):
    timestamp: str
    method: str
    path: str
    status: int
    duration_ms: float
    request_id: str


class EnvironmentConfigSection(AdminConfig):
    name: str
    settings: dict[str, Any]


class SmokeTestResult(AdminConfig):
    path: str
    name: str
    category: str
    auth_level: str
    status_code: int | None = None
    response_time_ms: float
    passed: bool
    error: str | None = None


class SmokeTestReport(AdminConfig):
    run_at: str
    environment: str
    total: int
    passed: int
    failed: int
    duration_ms: float
    all_critical_passed: bool
    results: list[SmokeTestResult]
