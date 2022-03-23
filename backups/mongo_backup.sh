#!/bin/sh

# Make sure to:
# 1) Name this file `backup.sh` and place it in /home/ubuntu
# 2) Run sudo apt install awscli to install the AWSCLI
# 3) Run aws configure (should use EC2 instance permissions)
# 4) Create S3 bucket for the backups and fill it in below (set a lifecycle rule to expire files older than X days in the bucket)
# 5) Run chmod +x backup.sh
# 6) Set up a daily backup at midnight via `crontab -e`:
#    0 0 * * * /home/ubuntu/backup.sh > /home/ubuntu/backup.log

export HOME=/home/ubuntu/

USER=ubuntu

DATE=`/bin/date +%Y-%m-%d`

HOST=localhost

# S3 bucket name
BUCKET=backups

# Mongo DB Name
MONGO_DBNAME=database

# Postgres DB Name
POSTGRES_DBNAME=database

# Log
echo "Backing up $HOST/$MONGO_DBNAME to s3://$BUCKET/ on $DATE";

# Stream the backup to S3 because it is tiny
# Dump from mongodb host into backup directory
/usr/bin/mongodump --archive --db $MONGO_DBNAME |  aws s3 cp --storage-class STANDARD_IA - s3://$BUCKET/mongo/$DATE.dump

# Log
echo "Backing up $HOST/$POSTGRES_DBNAME to s3://$BUCKET/ on $DATE";

# Stream the backup to S3 because it is tiny
# -Fc format is compressed by Postgres
/usr/bin/pg_dump -Fc $POSTRES_DBNAME | aws s3 cp --storage-class STANDARD_IA - s3://$BUCKET/postgres/$DATE.dump

echo "Finished Backups"