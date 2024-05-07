"""This module can be called from the command line to restore a Postgres database from a backup file.

Usually it is called by the ichrisbirch command line utility (located outside of this repo) to create a one time backup
with a description for particular events. Events are usually before a database migration or any change that might cause
database issues.

"""

import argparse

from ichrisbirch.config import get_settings
from ichrisbirch.scheduler.postgres_backup_restore import PostgresBackupRestore

settings = get_settings()

help_msg = """Backup the rds postgres database to S3.
\n
By default, the backup will be uploaded to S3 and not saved locally.
Pass arguments to change the default settings.
\n
Add a description for the reason why this backup is being created aside from the
regularly scheduled backups done by the scheduler.
"""

parser = argparse.ArgumentParser(description=help_msg, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--skip-upload', action='store_true', required=False, help='Upload to S3')
parser.add_argument('--save-local', action='store_true', required=False, help='Save the backup locally')
parser.add_argument('--description', required=False, help='Description of the backup')
args = parser.parse_args()
upload = not args.skip_upload
description = args.description or 'manual trigger'
description = ''.join([d.lower() for d in description]).replace(' ', '-')

pbr = PostgresBackupRestore(
    environment=settings.ENVIRONMENT,
    backup_bucket=settings.aws.s3_backup_bucket,
    source_host=settings.postgres.host,
    source_port=settings.postgres.port,
    source_username=settings.postgres.username,
    source_password=settings.postgres.password,
    show_command_output=True,
)

pbr.backup(upload=upload, save_local=args.save_local, backup_description=description)
