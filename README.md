# iChrisBirch Apps and Schtuff

- [1. Testing](#1-testing)
- [2. Nginx](#2-nginx)
  - [2.1. Dev Testing on Mac](#21-dev-testing-on-mac)
- [3. Set up pg\_cron](#3-set-up-pg_cron)
- [4. Backups](#4-backups)
- [5. Environment](#5-environment)
- [6. git-secret](#6-git-secret)
  - [6.1. Making a Secret](#61-making-a-secret)
  - [6.2. Getting a Secret](#62-getting-a-secret)
  - [6.3. Using git-secret with EC2 instance](#63-using-git-secret-with-ec2-instance)
    - [6.3.1. Make gpg key for EC2 instance](#631-make-gpg-key-for-ec2-instance)
      - [6.3.1.1. Local Machine](#6311-local-machine)
      - [6.3.1.2. EC2 Instance](#6312-ec2-instance)
  - [6.4. Make a gpg key for CICD](#64-make-a-gpg-key-for-cicd)
    - [6.4.1. Note for Ubuntu 20.04](#641-note-for-ubuntu-2004)
- [7. Configuration](#7-configuration)

## 1. Testing

=======

## 2. Nginx

Local Testing:

- Make sure to change `/etc/hosts` file:
  `127.0.0.1   localhost` --> `127.0.0.1 localhost api.localhost books.localhost`

### 2.1. Dev Testing on Mac

Docroot is: /usr/local/var/www

The default port has been set in /usr/local/etc/nginx/nginx.conf to 8080 so that
nginx can run without sudo.

nginx will load all files in /usr/local/etc/nginx/servers/.

To restart nginx after an upgrade:
  brew services restart nginx
Or, if you don't want/need a background service you can just run:
  /usr/local/opt/nginx/bin/nginx -g daemon off;

## 3. Set up pg_cron

Location: `/deploy`

1. pg_cron must be added to 'shared_preload_libraries'
   1. Reboot required
2. pg_cron runs in the default postgres database, then jobs can be moved to specific databases
3. For AWS RDS: <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL_pg_cron.html>
4. `pg_cron_setup.sql`

## 4. Backups

Location: `/backup_scripts`

1. Install AWS-CLI
2. `aws configure` - Use credentials for
MongDB Backup:
<https://www.cloudsavvyit.com/6059/how-to-set-up-automated-mongodb-backups-to-s3/>

Postgres Backup:

## 5. Environment

Location: `/`
`.env` - Holds all of the environment constants

- Choosing not to separate these for now, one file.

## 6. git-secret

[gpg cheatsheet](https://aws-labs.com/gpg-keys-cheatsheet/)

### 6.1. Making a Secret

1. `git secret init` - for new repository
2. `git secret tell ichrisbirch@gmail.com`
   1. This user has to have a public GPG key on THIS computer
3. `git secret tell 'user@email.com'`
   1. Import this user's public GPG key
4. `git secret add .env`
5. `git secret hide`
6. Add and commit new .secret file(s)

### 6.2. Getting a Secret

1. Git pull the .secret file(s)
2. `git secret reveal`

### 6.3. Using git-secret with EC2 instance

#### 6.3.1. Make gpg key for EC2 instance

##### 6.3.1.1. Local Machine

```bash
gpg --gen-key
# Real name: iChrisBirch EC2
# Email address: ec2@ichrisbirch.com

# Export and upload keys to EC2 Instance
gpg --export --armor "iChrisBirch EC2" > ec2-public.key
gpg --export-secret-key --armor "iChrisBirch EC2" > ec2-private.key
scp -i ~/.ssh/apps.pem ec2-public.key ubuntu@ichrisbirch:~
scp -i ~/.ssh/apps.pem ec2-private.key ubuntu@ichrisbirch:~

# Project Directory
git secret tell ec2@ichrisbirch.com
# to re-encrypt them with the new authorized user
git secret reveal
git secret hide
git add .
git commit -m 'ops: Update secrets with new authorized user'
git push
```

##### 6.3.1.2. EC2 Instance

```bash
# Import keys
gpg --import ec2-public.key
gpg --import ec2-private.key

# Project Directory
git pull
git secret reveal
```

### 6.4. Make a gpg key for CICD

```bash
# Generate new key, no passphrase
gpg --gen-key
# Export the secret key as one line, multiline not allowed
gpg --armor --export-secret-key datapointchris@github.com | tr '\n' ',' > cicd-gpg-key.gpg
# In the repository:
git secret reveal
git secret tell datapointchris@github.com
git secret hide
```

Add the key to the CICD environment secrets.
Add this to the CICD workflow, which will re-create the line breaks and import into gpg

```yaml
- name: "git-secret Reveal .env files"
  run: |
    # Import private key and avoid the "Inappropriate ioctl for device" error
    echo ${{ secrets.CICD_GPG_KEY }} | tr ',' '\n' | gpg --batch --yes --pinentry-mode loopback --import
    git secret reveal
```

#### 6.4.1. Note for Ubuntu 20.04

It is necessary to downgrade the version of gpg in MacOS to be compatible with the version running on Ubuntu 20.04, specifically the runners on GitHub Actions.
<https://github.com/sobolevn/git-secret/issues/760#issuecomment-1126163319>

```bash
brew uninstall git-secret
brew uninstall gpg
brew cleanup
brew install gnupg@2.2
# MUST add /usr/local/opt/gnupg@2.2/bin to PATH in dotfiles
brew install git-secret
# brew says it installs gnupg with git-secret, but after gpg still points to 2.2
git secret clean
git secret hide
```

SUCCESS!!!

## 7. Configuration

Location: `/`
`config.py` - Config classes for environments
