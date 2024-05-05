import logging
import os
import subprocess  # nosec
from pathlib import Path

import boto3
import pendulum

from ichrisbirch.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

start = pendulum.now()
filename_safe_timestamp = start.format('YYYY-MM-DDTHHmm')
dump_file_name = f'pg_dump-{filename_safe_timestamp}.dump'
dump_file_path = Path.cwd() / dump_file_name
env = settings.ENVIRONMENT


def dump_database():
    dump_command = [
        'pg_dump',
        f'--host={settings.postgres.host}',
        f'--username={settings.postgres.user}',
        f'--dbname={settings.postgres.user}',
        '--format=custom',
        f'--file={dump_file_path}',
    ]
    env = os.environ.copy()
    env['PGPASSWORD'] = settings.postgres.password
    logger.info('dumping postgres database')
    subprocess.run(dump_command, env=env)  # nosec
    logger.info(f'postgres data dumped: {dump_file_name}')


def upload_to_s3():
    s3 = boto3.resource('s3').Bucket(settings.aws.s3_backup_bucket)
    key = f'postgres/{dump_file_name}'
    logger.info(f'uploading to s3: {settings.aws.s3_backup_bucket}/postgres/{dump_file_name}')
    s3.upload_fileobj(dump_file_path.open('rb'), key)
    logger.info('successfully uploaded to s3')


def delete_dump_file():
    logger.info('deleting dump file')
    dump_file_path.unlink()
    logger.info('dump file deleted')


def postgres_backup_to_s3():
    logger.info(f'postgres backup to s3 started - {env}')
    dump_database()
    if settings.ENVIRONMENT == 'development':
        logger.info('development environment detected, skipping uploading to s3')
    else:
        upload_to_s3()
    delete_dump_file()

    elapsed = (pendulum.now() - start).in_words()
    logger.info(f'postgres backup to s3 completed - {elapsed}')


if __name__ == '__main__':
    postgres_backup_to_s3()
