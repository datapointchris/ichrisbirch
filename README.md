
Testing
=======
## Nginx
Local Testing:
- Make sure to change `/etc/hosts` file:
  `127.0.0.1   localhost` --> `127.0.0.1 localhost api.localhost books.localhost`

### Dev Testing on Mac
Docroot is: /usr/local/var/www

The default port has been set in /usr/local/etc/nginx/nginx.conf to 8080 so that
nginx can run without sudo.

nginx will load all files in /usr/local/etc/nginx/servers/.

To restart nginx after an upgrade:
  brew services restart nginx
Or, if you don't want/need a background service you can just run:
  /usr/local/opt/nginx/bin/nginx -g daemon off;






Set up pg_cron
================
Location: `/deploy`
1. pg_cron must be added to 'shared_preload_libraries'
   1. Reboot required
2. pg_cron runs in the default postgres database, then jobs can be moved to specific databases
3. For AWS RDS: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL_pg_cron.html
4. `pg_cron_setup.sql`



Backups
=======
Location: `/backup_scripts`
1. Install AWS-CLI
2. `aws configure` - Use credentials for 
MongDB Backup:
https://www.cloudsavvyit.com/6059/how-to-set-up-automated-mongodb-backups-to-s3/

Postgres Backup:



Environment
=============
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



Configuration
=============
Location: `/`
`config.py` - Config classes for environments
