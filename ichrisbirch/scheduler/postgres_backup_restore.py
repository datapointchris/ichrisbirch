import hashlib
import os
import subprocess  # nosec
from pathlib import Path

import boto3
import pendulum
import psycopg
import structlog

from ichrisbirch.config import get_settings
from ichrisbirch.util import find_project_root

logger = structlog.get_logger()


class PostgresBackupRestore:
    """Backing up or Restoring a Postgres Database in AWS.

    backup_description:
        used when calling the backup function for a specific purpose
        Default: 'scheduled'
    """

    def __init__(
        self,
        backup_bucket: str | None = None,
        source_host: str | None = None,
        source_port: str | None = None,
        source_username: str | None = None,
        source_password: str | None = None,
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

        self.source_host = source_host or self.settings.postgres.host
        self.source_port = source_port or self.settings.postgres.port
        self.source_username = source_username or self.settings.postgres.username
        self.source_password = source_password or self.settings.postgres.password

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
                    row_count = cur.fetchone()[0]
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
            size = cur.fetchone()[0]
        logger.info('database size collected', size_bytes=size)
        return size

    def _get_postgres_version(self) -> str:
        """Get PostgreSQL version string."""
        with self._get_db_connection() as conn, conn.cursor() as cur:
            cur.execute('SELECT version()')
            version = cur.fetchone()[0]
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
        backup_description: str,
        verbose=False,
    ) -> Path:
        timestamp = pendulum.now().format('YYYY-MM-DDTHHmm')
        backup_filename = f'backup-{timestamp}-{backup_description}.dump'
        backup_fullpath = out_dir / backup_filename
        command = [
            'pg_dumpall',
            f'--host={host}',
            f'--port={port}',
            f'--username={username}',
            '--no-password',
            f'--file={backup_fullpath}',
        ]
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
        upload=True,
        save_local=False,
        backup_description: str = 'scheduled',
    ) -> dict:
        """Create a database backup with comprehensive metadata.

        Returns a dict with backup results and metadata for saving to backup_history.
        """
        start = pendulum.now()
        created_at = start.to_iso8601_string()
        logger.info(f'started: postgres backup to s3 - {self.settings.ENVIRONMENT}')

        result = {
            'success': False,
            'filename': None,
            'size_bytes': None,
            'duration_seconds': None,
            's3_key': None,
            'local_path': None,
            'error_message': None,
            'table_snapshot': None,
            'postgres_version': None,
            'database_size_bytes': None,
            'checksum': None,
            'created_at': created_at,
        }

        try:
            # Collect metadata before backup
            result['table_snapshot'] = self._get_table_snapshot()
            result['postgres_version'] = self._get_postgres_version()
            result['database_size_bytes'] = self._get_database_size()

            # Create the backup
            backup_file = self._backup_database(
                host=self.source_host,
                port=self.source_port,
                username=self.source_username,
                password=self.source_password,
                out_dir=self.local_dir,
                backup_description=backup_description,
            )

            result['filename'] = backup_file.name
            result['size_bytes'] = backup_file.stat().st_size
            result['checksum'] = self._compute_checksum(backup_file)

            # Upload to S3 if requested
            if upload:
                result['s3_key'] = self._upload_to_s3(file=backup_file)

            # Handle local file
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

        return result

    def _download_from_s3(self, filename: Path | str):
        """Either a dump file name of a specific backup, or 'latest' which will get the latest backup."""
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

    def _restore(self, host, port, username, password, file: Path | str, verbose=False):
        """Restore the database in the dump file.

        NOTE: the --dbname used to connect is 'postgres' because it is used as the base database
        to issue the CREATE DATABASE command.  The database name to create is embedded in the dump file.
        --no-privileges because rdsadmin privilege GRANT and REVOKE will cause errors.
        """
        command = [
            'psql',
            f'--host={host}',
            f'--port={port}',
            f'--username={username}',
            '--no-password',
            f'--file={file}',
        ]
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
            command.append('--echo-all')

        logger.info(f'connecting to database: {host}:{port}')
        logger.info('starting: database restore')
        self._run_command(command, env={'PGPASSWORD': password})
        logger.info(f'restored to: {host}:{port}')

    def restore(self, filename: str | Path, skip_download=False, delete_local=False):
        start = pendulum.now()
        logger.info(f'started: postgres restore from s3 - {self.settings.ENVIRONMENT}')
        if skip_download:
            download_file = filename
        else:
            download_file = self._download_from_s3(filename)
        self._restore(
            host=self.target_host,
            port=self.target_port,
            username=self.target_username,
            password=self.target_password,
            file=download_file,
        )
        if not skip_download and delete_local:
            self._delete_file(Path(download_file))
        elapsed = (pendulum.now() - start).in_words()
        logger.info(f'postgres restore to s3 completed - {elapsed}')
