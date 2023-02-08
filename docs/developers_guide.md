# Developer's Guide

- [Developer's Guide](#developers-guide)
  - [Creating a Release](#creating-a-release)
- [ERRORS](#errors)
  - [Flask](#flask)
    - [ERROR](#error)
  - [Linux](#linux)
    - [ERROR](#error-1)
    - [Solution](#solution)
  - [Supervisor](#supervisor)
    - [ERROR](#error-2)
    - [Solution](#solution-1)
    - [ERROR](#error-3)
    - [Solution](#solution-2)
    - [ERROR](#error-4)
    - [Solution](#solution-3)
  - [NGINX](#nginx)
    - [ERROR](#error-5)
    - [Solution](#solution-4)
    - [Solution](#solution-5)
  - [API Postgres](#api-postgres)
    - [ERROR](#error-6)
- [SOLUTION](#solution-6)
- [New Server](#new-server)
  - [Change default shell to zsh and install all of the goodies](#change-default-shell-to-zsh-and-install-all-of-the-goodies)
- [First time](#first-time)
  - [DB](#db)
    - [Schemas](#schemas)
    - [Alembic](#alembic)
  - [Requirements](#requirements)
  - [Dev Requirements](#dev-requirements)
- [Notes](#notes)
  - [Alembic Revision](#alembic-revision)
  - [FastAPI Crud Endpoints](#fastapi-crud-endpoints)
- [Testing](#testing)

## Creating a Release

1. Change(s) should be committed/merged to `master`
2. run `/scripts/create-release X.X.X 'Release Description'

# ERRORS

==============================

## Flask

### ERROR

blank pages but no errors, try a different port.

- Sometimes the port is busy or used, but does not give a 'port in use' error

## Linux

### ERROR

ModuleNotFoundError: No module named 'cachecontrol' when running poetry:

### Solution

`sudo apt install python3-cachecontrol`

------------------------------

## Supervisor

### ERROR

supervisor.sock no such file

### Solution

make sure directories and files for logs are created.

### ERROR

BACKOFF can't find command... that is pointing to .venv

### Solution

Prod: Check that the project is installed
Dev: Check the symlink isn't broken

### ERROR

error: <class 'FileNotFoundError'>, [Errno 2] No such file or directory: file: /usr/local/Cellar/supervisor/4.2.5/libexec/lib/python3.11/site-packages/supervisor/xmlrpc.py line: 55

### Solution

Start and run supervisor with homebrew: `brew services start supervisor`

## NGINX

### ERROR

bind() to 0.0.0.0:80 failed (98: Address already in use)

### Solution

`sudo pkill -f nginx & wait $!`
`sudo systemctl start nginx`

__DEV__
bind() to 127.0.0.1:80 failed (13: Permission denied)

### Solution

NGINX is not running as root.  It does not run reliably with homebrew.
Use `sudo nginx -s reload` instead of homebrew.

## API Postgres

### ERROR

Local changes were working but nothing that connected to prod postgres.

`api.ichrisbirch.com/tasks/` - 502 Bad Gateway
`api.ichrisbirch.com` Success redirect to `/docs`
`ichrisbirch.com` redirects to www in browser but error with requests
`www.ichrisbirch.com/tasks/` - Internal Server Error
Can connect to prod server with DBeaver
Verified that the connection info is the same.
Seems that the API is not connecting to postgres instance

__api.macmini.local__
WORKING api.macmini.local/
WORKING api.macmini.local/docs
WORKING api.macmini.local/tasks
WORKING api.macmini.local/tasks/1
WORKING api.macmini.local/tasks/completed

__ichrisbirch.com__
WORKING api.ichrisbirch.com/
WORKING api.ichrisbirch.com/docs
ERROR api.ichrisbirch.com/tasks
ERROR api.ichrisbirch.com/tasks/1
ERROR api.ichrisbirch.com/tasks/completed

# SOLUTION

The issue was resolved by modifying the security group of the postgres instance to allow the ec2 instance to connect by allowing it's security group.

# New Server

==============================

## Change default shell to zsh and install all of the goodies

```bash
# Install ZSH
sudo apt update && sudo apt upgrade
sudo apt install zsh -y
sudo apt install neofetch -y

# Install oh-my-zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Get dotfiles (need access token)
git clone https://github.com/datapointchris/dotfiles.git ~/.dotfiles

# Symlink dotfiles
source ~/.dotfiles/symlinks-ec2

# Install bpytop
sudo apt install bpytop -y
```

# First time

==============================

## DB

### Schemas

SQLAlchemy cannot create the schemas, neither can alembic, have to create them manually first time
`create-schemas.py` to add the schemas

### Alembic

Run in `ichrisbirch`

Create the initial tables from the SQLAlchemy models (purpose of --autogenerate)
`alembic revision --autogenerate -m 'init_tables'`

Run the upgrade to actually create the tables
`alembic upgrade head`

## Requirements

Poetry

## Dev Requirements

Docker
tokei
tools

# Notes

==============================

## Alembic Revision

Run in `ichrisbirch`

1. Make the changes to the models and schemas

2. Run a revision to pickup changes in code
`alembic revision --autogenerate -m 'Add notes field to tasks table'`

> Note: If this doesn't work perfectly, you must edit the revision file

3. Run the upgrade in the environments

```bash
export ENVIRONMENT='development'
alembic upgrade head
```

## FastAPI Crud Endpoints

You have to specify keyword arguments after `db` because of the function signature with `*`
Order matters with endpoints, dynamic routes `route/endpoint/{id}` are last

# Testing

==============================
In order to run pytest, you have to set `ENVIRONMENT=development` so that the config can pick it up and set the correct variables.
Note: Config is not actually setting anything in tests, but the config is called in some of the files that are imported and it will error if not set.
