export HOME=/home/ubuntu/

### make the backup and then restore it and see if they are equivalent
### research how to test database backup integrity

HOST=localhost

# DB name
DBNAME=database

# S3 bucket name
BUCKET=backups

# Linux user account
USER=ubuntu

# Current time
TIME=`/bin/date +%d-%m-%Y-%T`

# Backup directory
DEST=/home/$USER/tmp

# Tar file of backup directory
TMP_FILE=$TIME.dump

# Create backup dir (-p to avoid warning if already exists)
/bin/mkdir -p $DEST

# Log
echo "Backing up $HOST/$DBNAME to s3://$BUCKET/ on $TIME";

# Dump from mongodb host into backup directory
/usr/bin/pg_dump -Fc $DBNAME > 

# Create tar of backup directory
/bin/tar cvf $TAR -C $DEST .

# Upload tar to s3
/usr/bin/aws s3 cp $TAR s3://$BUCKET/ --storage-class STANDARD_IA

# Remove tar file locally
/bin/rm -f $TAR

# Remove backup directory
/bin/rm -rf $DEST

# All done
echo "Backup available at https://s3.amazonaws.com/$BUCKET/$TIME.tar"