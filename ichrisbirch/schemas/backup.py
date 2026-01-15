import re
from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator


class BackupConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BackupCreate(BackupConfig):
    """Schema for creating a new backup."""

    description: str
    upload_to_s3: bool = True
    save_local: bool = False

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        cleaned = re.sub(r'[^a-z0-9-]', '', v.lower().replace(' ', '-'))
        if not cleaned:
            raise ValueError('Description must contain alphanumeric characters')
        if len(cleaned) > 50:
            raise ValueError('Description must be 50 characters or less')
        return cleaned


class TableSnapshot(BackupConfig):
    """Schema for table row count data."""

    schema_name: str
    table_name: str
    row_count: int


class TableSnapshotSummary(BackupConfig):
    """Schema for complete table snapshot."""

    tables: list[TableSnapshot]
    total_tables: int
    total_rows: int


class BackupRestoreSchema(BackupConfig):
    """Schema for restore event."""

    id: int
    backup_id: int
    restored_at: datetime
    restored_to_environment: str
    duration_seconds: float | None = None
    success: bool
    error_message: str | None = None
    restored_by_user_id: int | None = None


class Backup(BackupConfig):
    """Schema for backup history entry."""

    id: int
    filename: str
    description: str
    backup_type: str
    environment: str
    created_at: datetime
    deleted_at: datetime | None = None
    size_bytes: int | None = None
    duration_seconds: float | None = None
    s3_key: str | None = None
    local_path: str | None = None
    success: bool
    error_message: str | None = None
    table_snapshot: dict | None = None
    postgres_version: str | None = None
    database_size_bytes: int | None = None
    checksum: str | None = None
    triggered_by_user_id: int | None = None
    restores: list[BackupRestoreSchema] = []


class BackupResult(BackupConfig):
    """Schema for backup create response - excludes restores to avoid lazy load issues."""

    id: int
    filename: str
    description: str
    backup_type: str
    environment: str
    created_at: datetime
    deleted_at: datetime | None = None
    size_bytes: int | None = None
    duration_seconds: float | None = None
    s3_key: str | None = None
    local_path: str | None = None
    success: bool
    error_message: str | None = None
    table_snapshot: dict | None = None
    postgres_version: str | None = None
    database_size_bytes: int | None = None
    checksum: str | None = None
    triggered_by_user_id: int | None = None
