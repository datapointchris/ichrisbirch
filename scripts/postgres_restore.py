import argparse

from ichrisbirch.scheduler.postgres_backup_restore import PostgresBackupRestore

parser = argparse.ArgumentParser(
    description='Restore rds postgres database from S3 or local file.', formatter_class=argparse.RawTextHelpFormatter
)
parser.add_argument(
    '--skip-download',
    action='store_true',
    required=False,
    help='Skip downloading from S3, specify a local filepath when using this option',
)
parser.add_argument('--delete-local', action='store_true', required=False, help='Delete the downloaded backup after restore')
parser.add_argument(
    '--filename',
    required=True,
    help=(
        """Filename of the backup to restore.

        Can be one of the following:
        1) 'latest' to get the latest from s3 (does not work with local file)
        2) name of a specific backup file in s3 under the environment the script will be running under
        3) local path of restore file (MUST also specify --skip-download for this option)
        """
    ),
)
parser.add_argument('--environment', required=False, help='Environment')

restore_target = parser.add_argument_group('Restore Target', description="""All of the following arguments are required.""")
restore_target.add_argument('--target-host', required=True, help='Target host')
restore_target.add_argument('--target-port', required=True, help='Target port')
restore_target.add_argument('--target-username', required=True, help='Target username')
restore_target.add_argument('--target-password', required=True, help='Target password')
args = parser.parse_args()

args_dict = {
    'environment': args.environment,
    'target_host': args.target_host,
    'target_port': args.target_port,
    'target_username': args.target_username,
    'target_password': args.target_password,
    'show_command_output': True,
}

# remove unset args
args_dict = {k: v for k, v in args_dict.items() if v is not None}

pbr = PostgresBackupRestore(**args_dict)
pbr.restore(filename=args.filename, skip_download=args.skip_download, delete_local=args.delete_local)
