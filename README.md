# Standards

## Versioning
Each milestone is a new version.


## Technologies
Python 3.10.1
Postgres 14.2
Version managed by AWS
Version managed in Atlas


# How to Do Things

## Backups
1. Install AWS-CLI
2. `aws configure` - Use credentials for 
MongDB Backup:
https://www.cloudsavvyit.com/6059/how-to-set-up-automated-mongodb-backups-to-s3/

Postgres Backup:


## Environment

`.env` - Holds all of the environment constants
  - Choosing not to separate these for now, one file.

### .env-secret

#### Making a Secret
1. `git secret init` - for new repository
2. `git secret tell ichrisbirch@gmail.com`
   1. This user has to have a public GPG key on THIS computer
3. `git secret tell 'user@email.com'`
   1. Import this user's public GPG key
4. `git secret add .env`
5. `git secret hide`
6. Add and commit new .secret file(s)

#### Getting a Secret
1. Git pull the .secret file(s)
2. `git secret reveal`

### Deploy
What does this folder contain?
What do each of the files do/contain?

### Configuration
`config.py` - This file holds the config classes for each environment
