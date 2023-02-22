# Developer's Guide

- [1. Creating a Release](#1-creating-a-release)
- [2. ERRORS](#2-errors)
- [3. Flask](#3-flask)
- [4. Linux](#4-linux)
- [5. Supervisor](#5-supervisor)
- [6. NGINX](#6-nginx)
- [7. API Postgres](#7-api-postgres)
- [8. New Server](#8-new-server)
  - [8.1. Change default shell to zsh and install all of the goodies](#81-change-default-shell-to-zsh-and-install-all-of-the-goodies)
- [9. First time](#9-first-time)
  - [9.1. DB](#91-db)
    - [9.1.1. Schemas](#911-schemas)
    - [9.1.2. Alembic](#912-alembic)
  - [9.2. Requirements](#92-requirements)
  - [9.3. Dev Requirements](#93-dev-requirements)
- [10. Notes](#10-notes)
- [11. Alembic Revision](#11-alembic-revision)
- [12. FastAPI Crud Endpoints](#12-fastapi-crud-endpoints)
- [13. Testing](#13-testing)

## 1. Creating a Release

1. Change(s) should be committed/merged to `master`
2. run `/scripts/create-release X.X.X 'Release Description'

## 2. ERRORS

==============================

## 3. Flask

blank pages but no errors, try a different port.

- Sometimes the port is busy or used, but does not give a 'port in use' error

## 4. Linux

> **Error**  

ModuleNotFoundError: No module named 'cachecontrol' when running poetry:

> **Solution**  

`sudo apt install python3-cachecontrol`

------------------------------

## 5. Supervisor

> **Error**  

supervisor.sock no such file

> **Solution**  

make sure directories and files for logs are created.

> **Error**  

BACKOFF can't find command... that is pointing to .venv

> **Solution**  

Prod: Check that the project is installed
Dev: Check the symlink isn't broken

> **Error**  

```bash
error: <class 'FileNotFoundError'>, [Errno 2] No such file or directory: file: /usr/local/Cellar/supervisor/4.2.5/libexec/lib/python3.11/site-packages/supervisor/xmlrpc.py line: 55
```

> **Solution**  

Start and run supervisor with homebrew: `brew services start supervisor`

## 6. NGINX

> **Error**  

bind() to 0.0.0.0:80 failed (98: Address already in use)

> **Solution**  

`sudo pkill -f nginx & wait $!`
`sudo systemctl start nginx`

**DEV**
bind() to 127.0.0.1:80 failed (13: Permission denied)

> **Solution**  

NGINX is not running as root.  It does not run reliably with homebrew.
Use `sudo nginx -s reload` instead of homebrew.

## 7. API Postgres

> **Error**  

Local changes were working but nothing that connected to prod postgres.

`api.ichrisbirch.com/tasks/` - 502 Bad Gateway
`api.ichrisbirch.com` Success redirect to `/docs`
`ichrisbirch.com` redirects to www in browser but error with requests
`www.ichrisbirch.com/tasks/` - Internal Server Error
Can connect to prod server with DBeaver
Verified that the connection info is the same.
Seems that the API is not connecting to postgres instance

**api.macmini.local**
WORKING api.macmini.local/
WORKING api.macmini.local/docs
WORKING api.macmini.local/tasks
WORKING api.macmini.local/tasks/1
WORKING api.macmini.local/tasks/completed

**ichrisbirch.com**
WORKING api.ichrisbirch.com/
WORKING api.ichrisbirch.com/docs
ERROR api.ichrisbirch.com/tasks
ERROR api.ichrisbirch.com/tasks/1
ERROR api.ichrisbirch.com/tasks/completed

> **Solution**  

The issue was resolved by modifying the security group of the postgres instance to allow the ec2 instance to connect by allowing it's security group.

## 8. New Server

==============================

### 8.1. Change default shell to zsh and install all of the goodies

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

## 9. First time

==============================

### 9.1. DB

#### 9.1.1. Schemas

SQLAlchemy cannot create the schemas, neither can alembic, have to create them manually first time
`create-schemas.py` to add the schemas

#### 9.1.2. Alembic

Run in `ichrisbirch`

Create the initial tables from the SQLAlchemy models (purpose of --autogenerate)
`alembic revision --autogenerate -m 'init_tables'`

Run the upgrade to actually create the tables
`alembic upgrade head`

### 9.2. Requirements

Poetry

### 9.3. Dev Requirements

Docker
tokei
tools

## 10. Notes

==============================

## 11. Alembic Revision

Run in `ichrisbirch`

1. Make the changes to the models and schemas

2. Run a revision to pickup changes in code
`alembic revision --autogenerate -m 'Add notes field to tasks table'`

    > **Note**  
    > If this doesn't work perfectly, you must edit the revision file

3. Run the upgrade in the environments

```bash
export ENVIRONMENT='development'
alembic upgrade head
```

## 12. FastAPI Crud Endpoints

Order matters with endpoints, dynamic routes `route/endpoint/{id}` are last

## 13. Testing

==============================
In order to run pytest, you have to set `ENVIRONMENT=development` so that the config can pick it up and set the correct variables.
Note: Config is not actually setting anything in tests, but the config is called in some of the files that are imported and it will error if not set.
