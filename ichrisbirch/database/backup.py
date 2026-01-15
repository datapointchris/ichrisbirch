"""Database backup operations.

Creates PostgreSQL backups with metadata tracking, S3 upload, and automatic
persistence to backup_history table.

Can be run as a module:
    python -m ichrisbirch.database.backup --description "pre-migration"
    python -m ichrisbirch.database.backup --description "pre-migration" --save-local
    python -m ichrisbirch.database.backup --description "pre-migration" --skip-upload --save-local
"""

import hashlib
import os
import subprocess  # nosec
from pathlib import Path
from typing import Any

import boto3
import pendulum
import psycopg
import structlog

from ichrisbirch import models
from ichrisbirch.config import get_settings
from ichrisbirch.database.session import create_session
from ichrisbirch.util import find_project_root

logger = structlog.get_logger()


class DatabaseBackup:
    """Create PostgreSQL database backups with comprehensive metadata tracking."""

    def __init__(
        self,
        backup_bucket: str | None = None,
        source_host: str | None = None,
        source_port: str | None = None,
        source_username: str | None = None,
        source_password: str | None = None,
        base_dir: Path | None = None,
        show_command_output: bool = False,
        settings: Any | None = None,
    ):
        self.settings = settings or get_settings()
        self.show_command_output = show_command_output

        self.backup_bucket = backup_bucket or self.settings.aws.s3_backup_bucket
        self.bucket_prefix = f'{self.settings.ENVIRONMENT}/postgres'

        self.source_host = source_host or self.settings.postgres.host
        self.source_port = source_port or self.settings.postgres.port
        self.source_username = source_username or self.settings.postgres.username
        self.source_password = source_password or self.settings.postgres.password

        self.base_dir = base_dir or find_project_root()
        self.local_prefix = Path(f'{self.backup_bucket}/{self.settings.ENVIRONMENT}/postgres')
        self.local_dir = self.base_dir / self.local_prefix

    def _run_command(self, command: list, env: dict | None = None):
        env = env or {}
        local_env = os.environ | env
        try:
            output = subprocess.run(command, env=local_env, capture_output=True, check=True, text=True)  # nosec
        except subprocess.CalledProcessError as e:
            logger.error(f'COMMAND FAILED: {e}')
            for line in e.stdout.split('\n'):
                logger.info(line)
            for line in e.stderr.split('\n'):
                logger.error(line)
            raise SystemExit(1) from e
        if self.show_command_output:
            for line in output.stdout.split('\n'):
                logger.info(line)
            for line in output.stderr.split('\n'):
                logger.warning(line)

    def _get_db_connection(self) -> psycopg.Connection:
        """Get a database connection for metadata queries."""
        return psycopg.connect(
            host=self.source_host,
            port=self.source_port,
            user=self.source_username,
            password=self.source_password,
            dbname='ichrisbirch',
        )

    def _get_table_snapshot(self) -> dict:
        """Get all tables with row counts across all schemas."""
        logger.info('collecting table snapshot')
        tables = []
        total_rows = 0

        with self._get_db_connection() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT schemaname, tablename
                FROM pg_tables
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY schemaname, tablename
            """)
            table_list = cur.fetchall()

            for schema_name, table_name in table_list:
                try:
                    cur.execute(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}"')  # nosec
                    result_row = cur.fetchone()
                    row_count = result_row[0] if result_row else 0
                    tables.append(
                        {
                            'schema_name': schema_name,
                            'table_name': table_name,
                            'row_count': row_count,
                        }
                    )
                    total_rows += row_count
                except Exception as e:
                    logger.warning(f'could not count rows in {schema_name}.{table_name}: {e}')
                    tables.append(
                        {
                            'schema_name': schema_name,
                            'table_name': table_name,
                            'row_count': -1,
                        }
                    )

        snapshot = {
            'tables': tables,
            'total_tables': len(tables),
            'total_rows': total_rows,
        }
        logger.info('table snapshot collected', total_tables=len(tables), total_rows=total_rows)
        return snapshot

    def _get_database_size(self) -> int:
        """Get total database size in bytes."""
        with self._get_db_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT pg_database_size('ichrisbirch')")
            result = cur.fetchone()
            size = result[0] if result else 0
        logger.info('database size collected', size_bytes=size)
        return size

    def _get_postgres_version(self) -> str:
        """Get PostgreSQL version string."""
        with self._get_db_connection() as conn, conn.cursor() as cur:
            cur.execute('SELECT version()')
            result = cur.fetchone()
            version = result[0] if result else 'unknown'
        logger.info('postgres version collected', version=version)
        return version

    def _compute_checksum(self, file_path: Path) -> str:
        """Compute SHA256 checksum of file."""
        logger.info('computing checksum', file=str(file_path))
        sha256_hash = hashlib.sha256()
        with file_path.open('rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256_hash.update(chunk)
        checksum = sha256_hash.hexdigest()
        logger.info('checksum computed', checksum=checksum[:16] + '...')
        return checksum

    def _delete_file(self, file: Path):
        logger.info(f'deleting: {file}')
        file.unlink()
        logger.info(f'deleted: {file.name}')
        logger.info(f'deleting: ./{self.local_prefix}')
        dir = file.parent
        while dir != self.base_dir:
            try:
                dir.rmdir()
            except OSError:
                logger.warning(f'{dir} not empty, leaving in place')
                break
            dir = dir.parent
        else:
            logger.info(f'deleted: ./{self.local_prefix}')

    def _backup_database(
        self,
        host,
        port,
        username,
        password,
        out_dir: Path,
        backup_filename: str,
        verbose=False,
    ) -> Path:
        backup_fullpath = out_dir / backup_filename
        command = [
            'pg_dump',
            f'--host={host}',
            f'--port={port}',
            f'--username={username}',
            '--no-password',
            '--format=custom',
            '--dbname=ichrisbirch',
            f'--file={backup_fullpath}',
        ]
        if verbose:
            command.append('--verbose')

        logger.info(f'creating backup directory: {backup_fullpath.parent}')
        backup_fullpath.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f'connecting to database: {host}:{port}')
        logger.info('starting: database dump')
        self._run_command(command, env={'PGPASSWORD': password})
        logger.info(f'postgres data dumped: {backup_fullpath}')
        return backup_fullpath

    def _upload_to_s3(self, file: Path) -> str:
        """Upload file to S3 and return the S3 key."""
        s3 = boto3.resource('s3').Bucket(self.backup_bucket)
        key = f'{self.bucket_prefix}/{file.name}'
        logger.info(f'uploading to s3: {self.backup_bucket}/{key}')
        s3.upload_fileobj(file.open('rb'), Key=key)
        logger.info('upload completed')
        return key

    def backup(
        self,
        description: str,
        upload: bool = True,
        save_local: bool = False,
        backup_type: str = 'manual',
        user_id: int | None = None,
    ) -> models.BackupHistory:
        """Create a database backup and save to backup_history.

        Args:
            description: Short description of the backup reason
            upload: Upload to S3 (default True)
            save_local: Keep local copy (default False)
            backup_type: 'manual' or 'scheduled'
            user_id: ID of user who triggered backup (None for scheduled/CLI)

        Returns:
            BackupHistory record with all metadata
        """
        start = pendulum.now()
        logger.info(f'started: postgres backup - {self.settings.ENVIRONMENT}')

        # Generate filename upfront so we can save error records even if backup fails early
        timestamp = start.format('YYYY-MM-DDTHHmm')
        backup_filename = f'backup-{timestamp}-{description}.dump'

        result: dict[str, Any] = {
            'success': False,
            'filename': backup_filename,
            'size_bytes': None,
            'duration_seconds': None,
            's3_key': None,
            'local_path': None,
            'error_message': None,
            'table_snapshot': None,
            'postgres_version': None,
            'database_size_bytes': None,
            'checksum': None,
            'created_at': start,
        }

        try:
            result['table_snapshot'] = self._get_table_snapshot()
            result['postgres_version'] = self._get_postgres_version()
            result['database_size_bytes'] = self._get_database_size()

            backup_file = self._backup_database(
                host=self.source_host,
                port=self.source_port,
                username=self.source_username,
                password=self.source_password,
                out_dir=self.local_dir,
                backup_filename=backup_filename,
            )

            result['filename'] = backup_file.name
            result['size_bytes'] = backup_file.stat().st_size
            result['checksum'] = self._compute_checksum(backup_file)

            if upload:
                result['s3_key'] = self._upload_to_s3(file=backup_file)

            if save_local:
                result['local_path'] = str(backup_file)
            else:
                self._delete_file(backup_file)

            result['success'] = True
            elapsed = pendulum.now() - start
            result['duration_seconds'] = elapsed.total_seconds()
            logger.info(f'postgres backup completed - {elapsed.in_words()}')

        except Exception as e:
            logger.error(f'backup failed: {e}')
            result['error_message'] = str(e)
            result['duration_seconds'] = (pendulum.now() - start).total_seconds()

        with create_session(self.settings) as session:
            record = models.BackupHistory(
                filename=result['filename'],
                description=description,
                backup_type=backup_type,
                environment=self.settings.ENVIRONMENT,
                created_at=result['created_at'],
                size_bytes=result['size_bytes'],
                duration_seconds=result['duration_seconds'],
                s3_key=result['s3_key'],
                local_path=result['local_path'],
                success=result['success'],
                error_message=result['error_message'],
                table_snapshot=result['table_snapshot'],
                postgres_version=result['postgres_version'],
                database_size_bytes=result['database_size_bytes'],
                checksum=result['checksum'],
                triggered_by_user_id=user_id,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            logger.info('backup_history saved', backup_id=record.id, success=result['success'])

        return record


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Create a PostgreSQL database backup.',
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument('--description', required=True, help='Description of the backup')
    parser.add_argument('--skip-upload', action='store_true', help='Skip uploading to S3')
    parser.add_argument('--save-local', action='store_true', help='Save the backup locally')

    args = parser.parse_args()

    description = ''.join([d.lower() for d in args.description]).replace(' ', '-')

    db_backup = DatabaseBackup(show_command_output=True)
    record = db_backup.backup(
        description=description,
        upload=not args.skip_upload,
        save_local=args.save_local,
        backup_type='manual',
    )

    print()
    if record.success:
        print('Backup successful!')
        print(f'  Filename: {record.filename}')
        print(f'  Size: {record.size_bytes} bytes')
        print(f'  Duration: {record.duration_seconds:.2f} seconds')
        if record.s3_key:
            print(f'  S3 Key: {record.s3_key}')
        if record.local_path:
            print(f'  Local Path: {record.local_path}')
        if record.checksum:
            print(f'  Checksum: {record.checksum[:16]}...')
        print(f'  Saved to backup_history (id={record.id})')
    else:
        print('Backup failed!')
        print(f'  Error: {record.error_message}')
