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

from ichrisbirch.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


rds = boto3.client('rds')


def _create_rds_snapshot(db_name: str, snapshot_name: str):
    try:
        rds.create_db_snapshot(DBInstanceIdentifier=db_name, DBSnapshotIdentifier=snapshot_name)
        waiter = rds.get_waiter('db_snapshot_completed')
        waiter.wait(DBInstanceIdentifier=db_name, DBSnapshotIdentifier=snapshot_name)
        # get the size of the snapshot
        snapshot = rds.describe_db_snapshots(DBSnapshotIdentifier=snapshot_name)
        return snapshot
    except ClientError as e:
        logger.error(f'error creating rds snapshot: {e}')
        raise


def _export_rds_snapshot_to_s3(
    region: str,
    account_id: str,
    aws_role: str,
    bucket: str,
    bucket_prefix: str,
    snapshot_name: str,
):
    try:
        source_arn = f'arn:aws:rds:{region}:{account_id}:snapshot:{snapshot_name}'
        iam_role_arn = f'arn:aws:iam::{account_id}:{aws_role}'
        kms_key_arn = f'arn:aws:kms:{region}:{account_id}:{settings.aws.kms_key}'
        export_task = rds.start_export_task(
            ExportTaskIdentifier=snapshot_name,
            SourceArn=source_arn,
            S3BucketName=bucket,
            S3Prefix=bucket_prefix,
            IamRoleArn=iam_role_arn,
            KmsKeyId=kms_key_arn,
        )
        export_status = ''
        while export_status.lower() != 'complete':
            time.sleep(300)
            tasks = rds.describe_export_tasks(ExportTaskIdentifier=export_task['ExportTaskIdentifier'])
            export_status = tasks['ExportTasks'][0]['Status']
            percent_progress = tasks['ExportTasks'][0]['PercentProgress']
            logger.info(f'snapshot export status: {export_status.lower()}, progress: {percent_progress}%')
    except ClientError as e:
        logger.error(f'error exporting rds snapshot to s3: {e}')
        raise


def _delete_rds_snapshot(db_name: str, snapshot_name: str):
    try:
        rds.delete_db_snapshot(DBSnapshotIdentifier=snapshot_name)
        waiter = rds.get_waiter('db_snapshot_deleted')
        waiter.wait(DBInstanceIdentifier=db_name, DBSnapshotIdentifier=snapshot_name)
    except ClientError as e:
        logger.error(f'error deleting rds snapshot: {e}')
        raise


def postgres_snapshot_to_s3():
    bucket_prefix = 'postgres'
    start = pendulum.now()
    snapshot_name = f'{settings.postgres.database}-{start.format('YYYY-MM-DDTHHmm')}-snapshot'
    logger.info('postgres backup started')

    logger.info(f'creating rds snapshot: {snapshot_name}')
    snapshot = _create_rds_snapshot(db_name=settings.postgres.database, snapshot_name=snapshot_name)
    size_in_gibibytes = snapshot['DBSnapshots'][0]['AllocatedStorage']
    size_in_kilobytes = round(size_in_gibibytes / 1073741.824, 2)
    logger.info(f'snapshot created successfully: {size_in_kilobytes} KB')

    full_bucket_path = f's3://{settings.aws.s3_backup_bucket}/{bucket_prefix}/{snapshot_name}'
    logger.info(f'exporting snapshot: {full_bucket_path}')
    _export_rds_snapshot_to_s3(
        region=settings.aws.region,
        account_id=settings.aws.account_id,
        aws_role=settings.aws.postgres_backup_role,
        bucket=settings.aws.s3_backup_bucket,
        bucket_prefix=bucket_prefix,
        snapshot_name=snapshot_name,
    )
    logger.info('snapshot exported successfully')

    logger.info('deleting rds snapshot')
    _delete_rds_snapshot(db_name=settings.postgres.database, snapshot_name=snapshot_name)
    logger.info('snapshot deleted successfully')

    elapsed_time = (pendulum.now() - start).in_words()
    logger.info(f'postgres backup completed successfully: {elapsed_time}')


if __name__ == '__main__':
    postgres_snapshot_to_s3()
