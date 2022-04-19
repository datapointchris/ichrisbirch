# Standards

## Versioning
Each milestone is a new version.


## Technologies

### Python
Python 3.10.1

### Postgres
Postgres 14.2

### DynamoDB
Version managed by AWS

### MongoDB
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
What is the process?

### Deploy
What does this folder contain?
What do each of the files do/contain?

### Configuration
`config.py` - This file holds the config classes for each environment
