# Standards


## Git

### Branching
`{app_name}-{purpose-of-branch}

### Commits
Conventional Commits
https://gist.github.com/qoomon/5dfcdf8eec66a051ecd85625518cfd13

### Issues and Milestones
TBD
Each milestone is a new minor version


## Versioning
SemVer
https://semver.org


## Technologies
Python 3.10.1  
Postgres 14.2  
DynamoDB
MongoDB



# Deploy
Location: `/deploy`
`nginx.conf`
  1. Set the server name and static folder location

`supervisor.conf`
  1. Set the project name

1. Run `deploy.sh` script as sudo and let it copy all of the information
2. Make sure everything is started and running
   1. `sudo supervisorctl status <project-name>`
   2. `tail /var/log/nginx/error.log`



# Set up pg_cron
Location: `/deploy`
1. pg_cron must be added to 'shared_preload_libraries'
   1. Reboot required
2. pg_cron runs in the default postgres database, then jobs can be moved to specific databases
3. For AWS RDS: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL_pg_cron.html
4. `pg_cron_setup.sql`



# Backups
Location: `/backup_scripts`
1. Install AWS-CLI
2. `aws configure` - Use credentials for 
MongDB Backup:
https://www.cloudsavvyit.com/6059/how-to-set-up-automated-mongodb-backups-to-s3/

Postgres Backup:



# Environment
Location: `/`
`.env` - Holds all of the environment constants
  - Choosing not to separate these for now, one file.

## .env-secret

### Making a Secret
1. `git secret init` - for new repository
2. `git secret tell ichrisbirch@gmail.com`
   1. This user has to have a public GPG key on THIS computer
3. `git secret tell 'user@email.com'`
   1. Import this user's public GPG key
4. `git secret add .env`
5. `git secret hide`
6. Add and commit new .secret file(s)

### Getting a Secret
1. Git pull the .secret file(s)
2. `git secret reveal`



# Configuration
Location: `/`
`config.py` - Config classes for environments
