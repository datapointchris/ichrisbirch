"""This module can be called from the command line to restore a Postgres database from a backup file.

Usually it is called by the ichrisbirch command line utility (located outside of this repo) to create a one time backup with a description
for particular events. Events are usually before a database migration or any change that might cause database issues.
"""

import argparse
import logging

from ichrisbirch.scheduler.postgres_backup_restore import PostgresBackupRestore

ops_logger = logging.getLogger(__name__)

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
parser.add_argument('--description', required=True, help='Description of the backup')

backup_source = parser.add_argument_group(
    'Source to Backup',
    description="""If any of the following parameters are specified, they are all required.

                Otherwise, they will default to the database settings for the current environment, set with 'ENVIRONMENT'
                """,
)
backup_source.add_argument('--environment', required=False, help='Environment')
backup_source.add_argument('--source-host', required=False, help='Source host')
backup_source.add_argument('--source-port', required=False, help='Source port')
backup_source.add_argument('--source-username', required=False, help='Source username')
backup_source.add_argument('--source-password', required=False, help='Source password')

args = parser.parse_args()

required_as_group = [args.environment, args.source_host, args.source_port, args.source_username, args.source_password]
if any(required_as_group) and not all(required_as_group):
    missing = [arg for arg in required_as_group if not arg]
    print('Missing required source arguments, all must be specified if one is specified')
    for arg in missing:
        print(f'Missing Argument: {arg}')
    exit(1)

args_dict = {
    'environment': args.environment,
    'source_host': args.source_host,
    'source_port': args.source_port,
    'source_username': args.source_username,
    'source_password': args.source_password,
    'logger': ops_logger,
    'show_command_output': True,
}

# remove unset args
args_dict = {k: v for k, v in args_dict.items() if v is not None}
upload = not args.skip_upload
description = ''.join([d.lower() for d in args.description]).replace(' ', '-')

pbr = PostgresBackupRestore(**args_dict)
pbr.backup(upload=upload, save_local=args.save_local, backup_description=description)
