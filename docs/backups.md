# Backups

PostgreSQL database backups are managed through Python classes that handle backup creation, S3 upload, metadata tracking, and restoration.

## CLI Commands

```bash
# Create a backup (uploads to S3 by default)
icb db backup pre-migration

# Create a backup and keep local copy
icb db backup pre-migration --save-local

# Create local-only backup (skip S3 upload)
icb db backup pre-migration --skip-upload --save-local

# List recent backups in S3
icb db list

# Restore from backup
icb db restore latest --target-host localhost --target-port 5432 --target-username postgres --target-password secret
icb db restore backup-2024-01-15.dump --target-host db.example.com --target-port 5432 --target-username postgres --target-password secret
```

## Web Interface

Admin users can create and view backups from the Flask admin panel:

- **URL**: `/admin/backups/`
- **Features**: Create backups, browse S3 bucket contents, navigate folders

## API Endpoints

Admin-authenticated endpoints for backup operations:

```bash
# Create backup
POST /admin/backups/
{
  "description": "pre-migration",
  "upload_to_s3": true,
  "save_local": false
}

# List backup history
GET /admin/backups/

# Get specific backup
GET /admin/backups/{id}/
```

## Scheduled Backups

The scheduler service creates automatic daily backups at 1:30 AM. See `ichrisbirch/scheduler/jobs.py`.

## Architecture

### DatabaseBackup Class

Located in `ichrisbirch/database/backup.py`:

- Creates PostgreSQL dumps using `pg_dump`
- Collects metadata: table snapshots, database size, postgres version
- Computes SHA256 checksum
- Uploads to S3 with environment-based prefix
- Persists backup history to `admin.backup_history` table

### DatabaseRestore Class

Located in `ichrisbirch/database/restore.py`:

- Downloads backups from S3
- Restores using `pg_restore`
- Records restore operations to `admin.backup_restore` table

### Backup History

All backups are tracked in the `admin.backup_history` table with:

- Filename, description, backup type (manual/scheduled)
- Size, duration, checksum
- S3 key and/or local path
- Table snapshot (row counts per table)
- PostgreSQL version and database size
- Success status and error messages

## S3 Bucket Structure

```text
{bucket}/
  development/
    postgres/
      backup-2024-01-15T1200-description.dump
  testing/
    postgres/
      ...
  production/
    postgres/
      ...
```

## Running Backups Directly

For advanced usage, backups can be run as Python modules:

```bash
# With all options visible
python -m ichrisbirch.database.backup --description "pre-migration" --save-local
python -m ichrisbirch.database.restore --filename latest --target-host localhost ...
```
