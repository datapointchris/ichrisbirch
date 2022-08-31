# Project Structure



# First time
## DB
Run `backend/init_db.py`
Run `alembic revision --autogenerate -m 'init_tables'`
Run `alembic upgrade head`

## Requirements
Poetry

## Dev Requirements
Docker
tokei


### FastAPI Crud Endpoints
You have to specify keyword arguments after `db` because of the function signature with `*`
Order matters with endpoints, dynamic routes `route/endpoint/{id}` are last


# Testing
In order to run pytest, you have to set `ENVIRONMENT=development` so that the config
can pick it up and set the correct variables.
Note: Config is not actually setting anything in tests, but the config is called in some of the files that are imported and it will error if not set.


## For A Release
================
1. Checks
  - [ ] All tests passing
  - [ ] Test on local dev
  - [ ] Black formatting
  - [ ] Pylint checks
  - [ ] (optional) Test on `test` environment
    - [ ] subject to implementation

=====
TESTING
=====
Swap 2 and 3

2. Merge Feature Branch
  `git checkout master`
  `git merge feature/{feature}`

3. Update Version and Stats --> Run commands in `...euphoria/euphoria/` directory
   - [ ] Bump the version in the main `__init__.py` file in `euphoria` directory
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
  
4. Commit version stats files and create a version tag
  `git commit -am 'release: v0.3.0 - Migrate Databases'`
- [ ] Create a git tag after the bump so that the tag references the bump commit
  - [ ] git tag 'v0.3.0'
- [ ] Push branch and tags
  - [ ] git push --tags
- [ ] Pray to Dionysus