import logging
import os
import subprocess  # nosec
from pathlib import Path

import boto3
import pendulum

from ichrisbirch.config import get_settings

settings = get_settings()
logger = logging.getLogger('ops')


class PostgresBackupRestore:
    """Backing up or Restoring a Postgres Database in AWS.

    backup_description:
        used when calling the backup function for a specific purpose
        Default: 'scheduled'
    """

    def __init__(
        self,
        environment: str,
        backup_bucket: str,
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
        self.environment = environment
        self.show_command_output = show_command_output

        self.backup_bucket = backup_bucket
        self.bucket_prefix = f'{environment}/postgres'

        self.source_host = source_host
        self.source_port = source_port
        self.source_username = source_username
        self.source_password = source_password

        self.target_host = target_host
        self.target_port = target_port
        self.target_username = target_username
        self.target_password = target_password

        self.base_dir = base_dir or self._find_git_root()
        self.local_prefix = Path(f'{backup_bucket}/{environment}/postgres')
        self.local_dir = self.base_dir / self.local_prefix

    def _find_git_root(self, path: Path = Path.cwd()) -> Path:
        git_root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=path)  # nosec
        return Path(git_root.decode().strip())

    def _run_command(self, command: list, env: dict = {}):
        local_env = os.environ | env
        try:
            output = subprocess.run(command, env=local_env, capture_output=True, check=True, text=True)  # nosec
        except subprocess.CalledProcessError as e:
            logger.error(f'COMMAND FAILED: {e}')
            for line in e.stdout.split('\n'):
                logger.info(line)
            for line in e.stderr.split('\n'):
                logger.error(line)
            raise SystemExit(1)
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

    def _upload_to_s3(self, file: Path):
        s3 = boto3.resource('s3').Bucket(self.backup_bucket)
        key = f'{self.bucket_prefix}/{file.name}'
        logger.info(f'uploading to s3: {self.backup_bucket}/{key}')
        s3.upload_fileobj(file.open('rb'), Key=key)
        logger.info('upload completed')

    def backup(
        self,
        upload=True,
        save_local=False,
        backup_description: str = 'scheduled',
    ):
        start = pendulum.now()
        logger.info(f'started: postgres backup to s3 - {self.environment}')
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
        logger.info(f'postgres backup to s3 completed - {elapsed}')

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

    def restore(self, filename: str | Path, download=True, save_local=True):
        start = pendulum.now()
        logger.info(f'started: postgres restore from s3 - {self.environment}')
        if download:
            download_file = self._download_from_s3(filename)
        else:
            download_file = filename
        self._restore(
            host=self.target_host,
            port=self.target_port,
            username=self.target_username,
            password=self.target_password,
            file=download_file,
        )
        if download and not save_local:
            self._delete_file(Path(download_file))
        elapsed = (pendulum.now() - start).in_words()
        logger.info(f'postgres backup to s3 completed - {elapsed}')


if __name__ == '__main__':
    pbr = PostgresBackupRestore(
        environment=settings.ENVIRONMENT,
        backup_bucket=settings.aws.s3_backup_bucket,
        source_host=settings.postgres.host,
        source_port=settings.postgres.port,
        source_username=settings.postgres.username,
        source_password=settings.postgres.password,
        target_host='localhost',
        target_port='5432',
        target_username='postgres',
        target_password='postgres',  # nosec
    )
    pbr.backup()
    pbr.restore('latest')
