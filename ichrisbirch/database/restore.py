"""Database restore operations.

Restores PostgreSQL database from backups with automatic persistence to
backup_restores table.

Can be run as a module:
    python -m ichrisbirch.database.restore --filename latest \
        --target-host HOST --target-port PORT \
        --target-username USER --target-password PASS
    python -m ichrisbirch.database.restore --filename backup-2024-01-15.dump \
        --target-host HOST ...
    python -m ichrisbirch.database.restore --filename /local/path.dump \
        --skip-download --target-host HOST ...
"""

import os
import subprocess  # nosec
from pathlib import Path
from typing import Any

import boto3
import pendulum
import structlog
from sqlalchemy import select

from ichrisbirch import models
from ichrisbirch.config import get_settings
from ichrisbirch.database.session import create_session
from ichrisbirch.util import find_project_root

logger = structlog.get_logger()


class DatabaseRestore:
    """Restore PostgreSQL database from backups with tracking."""

    def __init__(
        self,
        backup_bucket: str | None = None,
        target_host: str | None = None,
        target_port: str | None = None,
        target_username: str | None = None,
        target_password: str | None = None,
        base_dir: Path | None = None,
        show_command_output: bool = False,
    ):
        self.settings = get_settings()
        self.show_command_output = show_command_output

        self.backup_bucket = backup_bucket or self.settings.aws.s3_backup_bucket
        self.bucket_prefix = f'{self.settings.ENVIRONMENT}/postgres'

        self.target_host = target_host
        self.target_port = target_port
        self.target_username = target_username
        self.target_password = target_password

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

    def _download_from_s3(self, filename: str) -> Path:
        """Download backup from S3.

        Args:
            filename: Either a dump filename or 'latest' for most recent backup

        Returns:
            Path to downloaded file
        """
        s3 = boto3.resource('s3').Bucket(self.backup_bucket)
        if filename == 'latest':
            objects = s3.objects.filter(Prefix=f'{self.bucket_prefix}/')
            latest = max(objects, key=lambda obj: obj.last_modified)
            key = latest.key
        else:
            key = f'{self.bucket_prefix}/{filename}'

        download_path = self.local_dir / Path(key).name
        logger.info(f'creating download directory: {download_path.parent}')
        download_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f'downloading from s3: {self.backup_bucket}/{key}')
        s3.download_fileobj(key, download_path.open('wb'))
        logger.info(f'download location: {download_path}')
        return download_path

    def _restore_database(self, host, port, username, password, file: Path, verbose=False):
        """Restore the database from dump file.

        NOTE: --dbname=postgres is used as the base database to issue CREATE DATABASE.
        The database name is embedded in the dump file.
        --no-privileges because rdsadmin privilege GRANT and REVOKE will cause errors.
        """
        command = [
            'pg_restore',
            f'--host={host}',
            f'--port={port}',
            f'--username={username}',
            '--no-password',
            '--create',
            '--no-privileges',
            '--dbname=postgres',
            str(file),
        ]
        if verbose:
            command.append('--verbose')

        logger.info(f'connecting to database: {host}:{port}')
        logger.info('starting: database restore')
        self._run_command(command, env={'PGPASSWORD': password})
        logger.info(f'restored to: {host}:{port}')

    def _find_backup_record(self, filename: str) -> models.BackupHistory | None:
        """Find BackupHistory record by filename."""
        with create_session(self.settings) as session:
            query = select(models.BackupHistory).where(models.BackupHistory.filename == filename)
            return session.scalar(query)

    def restore(
        self,
        filename: str,
        skip_download: bool = False,
        delete_local: bool = False,
        user_id: int | None = None,
    ) -> models.BackupRestore:
        """Restore database from backup and save to backup_restores.

        Args:
            filename: Backup filename, 'latest', or local path (with skip_download)
            skip_download: Use local file instead of downloading from S3
            delete_local: Delete local file after restore
            user_id: ID of user who triggered restore (None for CLI)

        Returns:
            BackupRestore record with restore details
        """
        start = pendulum.now()
        logger.info(f'started: postgres restore - {self.settings.ENVIRONMENT}')

        result: dict[str, Any] = {
            'success': False,
            'duration_seconds': None,
            'error_message': None,
            'restored_at': start,
            'backup_id': None,
            'actual_filename': None,
        }

        try:
            if skip_download:
                restore_file = Path(filename)
                result['actual_filename'] = restore_file.name
            else:
                restore_file = self._download_from_s3(filename)
                result['actual_filename'] = restore_file.name

            backup_record = self._find_backup_record(result['actual_filename'])
            if backup_record:
                result['backup_id'] = backup_record.id
                logger.info('found backup_history record', backup_id=backup_record.id)
            else:
                logger.warning('no backup_history record found for filename', filename=result['actual_filename'])

            self._restore_database(
                host=self.target_host,
                port=self.target_port,
                username=self.target_username,
                password=self.target_password,
                file=restore_file,
            )

            if not skip_download and delete_local:
                self._delete_file(restore_file)

            result['success'] = True
            elapsed = pendulum.now() - start
            result['duration_seconds'] = elapsed.total_seconds()
            logger.info(f'postgres restore completed - {elapsed.in_words()}')

        except Exception as e:
            logger.error(f'restore failed: {e}')
            result['error_message'] = str(e)
            result['duration_seconds'] = (pendulum.now() - start).total_seconds()

        with create_session(self.settings) as session:
            if result['backup_id'] is None and result['actual_filename']:
                logger.info('creating stub backup_history record for untracked backup')
                stub_backup = models.BackupHistory(
                    filename=result['actual_filename'],
                    description='untracked-restore',
                    backup_type='unknown',
                    environment='unknown',
                    created_at=pendulum.now(),
                    success=True,
                )
                session.add(stub_backup)
                session.flush()
                result['backup_id'] = stub_backup.id
                logger.info('stub backup_history created', backup_id=stub_backup.id)

            record = models.BackupRestore(
                backup_id=result['backup_id'],
                restored_at=result['restored_at'],
                restored_to_environment=self.settings.ENVIRONMENT,
                duration_seconds=result['duration_seconds'],
                success=result['success'],
                error_message=result['error_message'],
                restored_by_user_id=user_id,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            logger.info('backup_restore saved', restore_id=record.id, success=result['success'])

        return record


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Restore a PostgreSQL database from backup.',
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        '--filename',
        required=True,
        help="Backup filename, 'latest' for most recent, or local path with --skip-download",
    )
    parser.add_argument('--skip-download', action='store_true', help='Use local file instead of S3')
    parser.add_argument('--delete-local', action='store_true', help='Delete local file after restore')

    target = parser.add_argument_group('Target Database', description='All target options are required.')
    target.add_argument('--target-host', required=True, help='Target database host')
    target.add_argument('--target-port', required=True, help='Target database port')
    target.add_argument('--target-username', required=True, help='Target database username')
    target.add_argument('--target-password', required=True, help='Target database password')

    args = parser.parse_args()

    db_restore = DatabaseRestore(
        target_host=args.target_host,
        target_port=args.target_port,
        target_username=args.target_username,
        target_password=args.target_password,
        show_command_output=True,
    )
    record = db_restore.restore(
        filename=args.filename,
        skip_download=args.skip_download,
        delete_local=args.delete_local,
    )

    print()
    if record.success:
        print('Restore successful!')
        print(f'  Backup ID: {record.backup_id}')
        print(f'  Restored to: {record.restored_to_environment}')
        print(f'  Duration: {record.duration_seconds:.2f} seconds')
        print(f'  Saved to backup_restores (id={record.id})')
    else:
        print('Restore failed!')
        print(f'  Error: {record.error_message}')
