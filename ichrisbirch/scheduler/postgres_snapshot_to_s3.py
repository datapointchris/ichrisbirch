"""Create RDS Postgres Snapshot and Export to S3.

Description:
1. Create a snapshot of RDS Postgres instance
2. Export to an S3 bucket
3. Delete the snapshot from RDS for cost savings

$(usage)

Requirements:
1. `awscli` installed, either locally or on the EC2 instance if running there.
2. Executor of script to have the following permissions:
  1. RDS create-db-snapshot
  2. RDS start-export-task
  3. RDS delete-db-snapshot
Locally: user or IAM credentials must have these permissions
EC2: the instance *should* have the necessary permissions through a security group or IAM role
"""

import logging
import time

import boto3
import pendulum
from botocore.exceptions import ClientError

from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings


class AwsRdsSnapshotS3:
    """Class for creating a snapshot from an RDS instance and exporting to S3."""

    def __init__(self, logger: logging.Logger, settings: Settings):
        self.logger = logger
        self.environment = settings.ENVIRONMENT
        self.bucket_prefix = f'{self.environment}/postgres'
        self.backup_bucket = settings.aws.s3_backup_bucket
        self.db_name = 'ichrisbirch-pg16'

        self.region = settings.aws.region
        self.account_id = settings.aws.account_id
        self.aws_role = settings.aws.postgres_backup_role
        self.kms_key = settings.aws.kms_key

        self.rds = boto3.client('rds', region_name=self.region)

    def _snapshot_size_in_kb(self, snapshot):
        size_in_gibibytes = snapshot['DBSnapshots'][0].get('AllocatedStorage', 0)
        size_in_kilobytes = round(size_in_gibibytes / 1073741.824, 2)
        if size_in_kilobytes < 1:
            self.logger.warning('snapshot size is < 1 KB, check for errors in snapshot creation')
        return size_in_kilobytes

    def _create_rds_snapshot(self, snapshot_name: str):
        try:
            self.rds.create_db_snapshot(DBInstanceIdentifier=self.db_name, DBSnapshotIdentifier=snapshot_name)
            waiter = self.rds.get_waiter('db_snapshot_completed')
            waiter.wait(DBInstanceIdentifier=self.db_name, DBSnapshotIdentifier=snapshot_name)
            snapshot = self.rds.describe_db_snapshots(DBSnapshotIdentifier=snapshot_name)
            return snapshot
        except ClientError as e:
            self.logger.error(f'error creating rds snapshot: {e}')
            raise

    def _export_rds_snapshot_to_s3(
        self,
        snapshot_name: str,
    ):
        try:
            source_arn = f'arn:aws:rds:{self.region}:{self.account_id}:snapshot:{snapshot_name}'
            iam_role_arn = f'arn:aws:iam::{self.account_id}:{self.aws_role}'
            kms_key_arn = f'arn:aws:kms:{self.region}:{self.account_id}:{self.kms_key}'
            export_task = self.rds.start_export_task(
                ExportTaskIdentifier=snapshot_name,
                SourceArn=source_arn,
                S3BucketName=self.backup_bucket,
                S3Prefix=self.bucket_prefix,
                IamRoleArn=iam_role_arn,
                KmsKeyId=kms_key_arn,
            )
            export_status = ''
            while export_status.lower() != 'complete':
                time.sleep(300)
                tasks = self.rds.describe_export_tasks(ExportTaskIdentifier=export_task['ExportTaskIdentifier'])
                export_status = tasks['ExportTasks'][0]['Status']
                percent_progress = tasks['ExportTasks'][0]['PercentProgress']
                self.logger.info(f'rds snapshot export status: {export_status.lower()}, progress: {percent_progress}%')
        except ClientError as e:
            self.logger.error(f'error exporting rds snapshot to s3: {e}')
            raise

    def _delete_rds_snapshot(self, snapshot_name: str):
        try:
            self.rds.delete_db_snapshot(DBSnapshotIdentifier=snapshot_name)
            waiter = self.rds.get_waiter('db_snapshot_deleted')
            waiter.wait(DBInstanceIdentifier=self.db_name, DBSnapshotIdentifier=snapshot_name)
        except ClientError as e:
            self.logger.error(f'error deleting rds snapshot: {e}')
            raise

    def snapshot(self):
        self.logger.info('rds snapshot started')
        start = pendulum.now()
        timestamp = start.format('YYYY-MM-DDTHHmm')
        snapshot_name = f'snapshot-{timestamp}'
        full_bucket_path = f's3://{self.backup_bucket}/{self.bucket_prefix}/{snapshot_name}'

        self.logger.info(f'creating rds snapshot: {snapshot_name}')
        snapshot = self._create_rds_snapshot(snapshot_name=snapshot_name)
        self.logger.info(f'created rds snapshot: {self._snapshot_size_in_kb(snapshot)} KB')

        self.logger.info('exporting rds snapshot to s3')
        self._export_rds_snapshot_to_s3(snapshot_name=snapshot_name)
        self.logger.info(f'exported rds snapshot: {full_bucket_path}')

        self.logger.info('deleting rds snapshot')
        self._delete_rds_snapshot(snapshot_name=snapshot_name)
        self.logger.info('deleted rds snapshot')

        elapsed_time = (pendulum.now() - start).in_words()
        self.logger.info(f'rds snapshot completed: {elapsed_time}')


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    rds_snap = AwsRdsSnapshotS3(logger=logger, settings=get_settings())
    rds_snap.snapshot()
