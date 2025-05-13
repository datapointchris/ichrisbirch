import logging
import os
import subprocess  # nosec
from pathlib import Path

import boto3
import pendulum

from ichrisbirch.config import Settings
from ichrisbirch.util import find_project_root


class PostgresBackupRestore:
    """Backing up or Restoring a Postgres Database in AWS.

    backup_description:
        used when calling the backup function for a specific purpose
        Default: 'scheduled'
    """

    def __init__(
        self,
        settings: Settings,
        logger: logging.Logger,
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
        self.logger = logger
        self.settings = settings
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

    def _run_command(self, command: list, env: dict = {}):
        local_env = os.environ | env
        try:
            output = subprocess.run(command, env=local_env, capture_output=True, check=True, text=True)  # nosec
        except subprocess.CalledProcessError as e:
            self.logger.error(f'COMMAND FAILED: {e}')
            for line in e.stdout.split('\n'):
                self.logger.info(line)
            for line in e.stderr.split('\n'):
                self.logger.error(line)
            raise SystemExit(1)
        if self.show_command_output:
            for line in output.stdout.split('\n'):
                self.logger.info(line)
            for line in output.stderr.split('\n'):
                self.logger.warning(line)

    def _delete_file(self, file: Path):
        self.logger.info(f'deleting: {file}')
        file.unlink()
        self.logger.info(f'deleted: {file.name}')
        self.logger.info(f'deleting: ./{self.local_prefix}')
        dir = file.parent
        while dir != self.base_dir:
            try:
                dir.rmdir()
            except OSError:
                self.logger.warning(f'{dir} not empty, leaving in place')
                break
            dir = dir.parent
        else:
            self.logger.info(f'deleted: ./{self.local_prefix}')

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

        self.logger.info(f'creating backup directory: {backup_fullpath.parent}')
        backup_fullpath.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info(f'connecting to database: {host}:{port}')
        self.logger.info('starting: database dump')
        self._run_command(command, env={'PGPASSWORD': password})
        self.logger.info(f'postgres data dumped: {backup_fullpath}')
        return backup_fullpath

    def _upload_to_s3(self, file: Path):
        s3 = boto3.resource('s3').Bucket(self.backup_bucket)
        key = f'{self.bucket_prefix}/{file.name}'
        self.logger.info(f'uploading to s3: {self.backup_bucket}/{key}')
        s3.upload_fileobj(file.open('rb'), Key=key)
        self.logger.info('upload completed')

    def backup(
        self,
        upload=True,
        save_local=False,
        backup_description: str = 'scheduled',
    ):
        start = pendulum.now()
        self.logger.info(f'started: postgres backup to s3 - {self.settings.ENVIRONMENT}')
        backup = self._backup_database(
            host=self.source_host,
            port=self.source_port,
            username=self.source_username,
            password=self.source_password,
            out_dir=self.local_dir,
            backup_description=backup_description,
        )
        if upload:
            self._upload_to_s3(file=backup)
        if not save_local:
            self._delete_file(backup)
        elapsed = (pendulum.now() - start).in_words()
        self.logger.info(f'postgres backup to s3 completed - {elapsed}')

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
        self.logger.info(f'creating download directory: {download_path.parent}')
        download_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info(f'downloading from s3: {self.backup_bucket}/{key}')
        s3.download_fileobj(key, download_path.open('wb'))
        self.logger.info(f'download location: {download_path}')
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

        self.logger.info(f'connecting to database: {host}:{port}')
        self.logger.info('starting: database restore')
        self._run_command(command, env={'PGPASSWORD': password})
        self.logger.info(f'restored to: {host}:{port}')

    def restore(self, filename: str | Path, skip_download=False, delete_local=False):
        start = pendulum.now()
        self.logger.info(f'started: postgres restore from s3 - {self.settings.ENVIRONMENT}')
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
        self.logger.info(f'postgres restore to s3 completed - {elapsed}')
