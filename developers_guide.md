# Project Structure

# ERRORS
==============================
## Flask:
### Error:
blank pages but no errors, try a different port.
  - Sometimes the port is busy or used, but does not give a 'port in use' error


## Linux
### Error:
ModuleNotFoundError: No module named 'cachecontrol' when running poetry:
### Solution
`sudo apt install python3-cachecontrol`


## Poetry
### Error:
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
### Error:
supervisor.sock no such file
### Solution
make sure directories and files for logs are created.

### Error:
BACKOFF can't find command... that is pointing to .venv
### Solution
Prod: Check that the project is installed
Dev: Check the symlink isn't broken


## NGINX
### Error:
bind() to 0.0.0.0:80 failed (98: Address already in use)
### Solution
`sudo pkill -f nginx & wait $!`
`sudo systemctl start nginx`


# New Server
==============================





# First time
==============================

## DB
`init_db.py` to add the schemas
`alembic revision --autogenerate -m 'init_tables'`
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
`alembic revision --autogenerate -m $VERSION`
TODO: Do I run `alembic upgrade head` in prod environment?


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