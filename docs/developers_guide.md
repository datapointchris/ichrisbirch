# Project Structure

# ERRORS
==============================
## Flask:
### ERROR
blank pages but no errors, try a different port.
  - Sometimes the port is busy or used, but does not give a 'port in use' error


## Linux
### ERROR
ModuleNotFoundError: No module named 'cachecontrol' when running poetry:
### Solution
`sudo apt install python3-cachecontrol`

------------------------------
TODO: [2022/12/28] - Check if this is the case in next version
I Believe this below part is no longer necessary.
## Poetry
### ERROR
Can not execute `setup.py` since setuptools is not available in the build environment:
### Solution
Poetry is not updated in Linux yet, so compatibility with requiring or removing setuptools.
MUST do the following:
:: Dev (MacOS) :: _Poetry Version 1.2.2_
`poetry export > requirments.txt`
:: Prod (Linux) :: _Poetry Version 1.1.12_
`sudo rm -rf .venv`
`python -m venv .venv`
`source .venv/bin/activate`
`python -m pip install -r requirements.txt`
`python -m pip install -e .`
This last command installs the package at that location, but in editable mode.
I don't believe this should be editable mode, but it is the only way to put the project
root here.
TODO: [2022/11/05] - Find out a better way for project root than editable


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


## NGINX
### ERROR
bind() to 0.0.0.0:80 failed (98: Address already in use)
### Solution
`sudo pkill -f nginx & wait $!`
`sudo systemctl start nginx`


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





# First time
==============================

## DB

### Schemas
SQLAlchemy cannot create the schemas, neither can alembic, have to create them manually first time
`create-schemas.py` to add the schemas

### Alembic
Run in `euphoria/backend/`

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

Run in `euphoria/backend/`

1. Make the changes to the models and schemas

2. Run a revision to pickup changes in code
`alembic revision --autogenerate -m 'Add notes field to tasks table'`
> Note: If this doesn't work perfectly, you must edit the revision file

3. Do the upgrade to the tables
> __Note:__ Run in all environments!
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


## For A Release
==============================
1. Checks
  - [ ] All tests passing
  - [ ] Test on local dev
  - [ ] Black formatting
  - [ ] Pylint checks
  - [ ] (optional) Test on `test` environment
    - [ ] subject to implementation

2. Update Version and Stats --> Run commands in `...euphoria/euphoria/` directory
   - [ ] Bump the version in the main `__init__.py` file in `euphoria` directory
   - [ ] Bump the version in `pyproject.toml`
   - [ ] Create an alembic migration with the release - Run in `...euphoria/euphoria/`
    `alembic revision --autogenerate -m {version}`
   - [ ] Create a new stats file json and text
    `tokei . --exclude .venv --exclude euphoria/backend/alembic/versions/ > euphoria/version_stats/{version}lines_of_code.txt`
    `tokei . --exclude .venv --exclude euphoria/backend/alembic/versions/ -o json > euphoria/version_stats/{version}lines_of_code.json`
   - [ ] Create a Coverage Report
    `pytest --cov`
    `coverage report -m > euphoria/version_stats/{version}/coverage.txt`
    `coverage json -o euphoria/version_stats/{version}/coverage.json`

   - [ ] Run Wily Code Complexity
   - [ ] wily does not have json output at the moment
    `wily diff . -r master > euphoria/version_stats/{version}/complexity.txt`
  
3. Commit version stats files and create a version tag
  `git commit -am 'release: v0.3.0 - Migrate Databases'`
- [ ] Create a git tag after the bump so that the tag references the bump commit
  - [ ] git tag 'v0.3.0'
- [ ] Push branch and tags
  - [ ] git push --tags
- [ ] Pray to Dionysus

4. Merge Feature Branch
  `git checkout master`
  `git merge feature/{feature}`

5. Re-install project
6. `poetry install`