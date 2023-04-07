# Changelog

## Misc

1. [X] Take code out of `__init__.py` files
   1. [X] Put them in `main.py` for the module or name of module
   2. [X] Import the names in the `__init__.py` file for better top level imports
2. [X] Main Site Navigation
   1. [X] Put this on base page that all pages inherit from
   2. [X] Inherit CSS as well
3. [ ] Restructure site so that all apps are top level
      1. [X] events
      2. [X] countdowns
      3. [X] journal
      4. [X] habits

## v0.2.0 --> Move databases (Postgres, MongoDB, DynamoDB) to their own Servers

---
Prod only, further ahead will figure out how to sync dev and "testing" (god help me) to the prod environment

- [X] pg_cron and update task priorities
- [X] MongoDB move to Atlas

## v0.3.0 --> Get rid of Flask-SQLAlchemy and Migrate Databases

- [X] Use regular SQLAlchemy instead.
- [X] Countdowns -> SQLAlchemy
- [ ] Apartments -> MongoDB
  - [ ] Skipping for now
- [X] Simplify Journal Entry MongoDB
- [X] Get rid of Events dict
  - [X] Maybe with Pydantic Models

## v0.4.0 --> Migrate Databases

- [X] Alembic
- [X] <https://alembic.sqlalchemy.org/en/latest/tutorial.html>

### v0.4.1 --> Hotfix: Add Stats to release

- [X] Output of tokei
- [X] Pytest with coverage
- [X] wily
- [X] Make it easy to add more in the future

## v0.5.0 --> FastAPI and Nginx

- FastAPI Course
- [X] <https://academy.christophergs.com/courses/fastapi-for-busy-engineers/curriculum>
API is being run on a different port/subdomain
api.ichrisbirch.com
<https://adamtheautomator.com/nginx-subdomain/>
<https://hackprogramming.com/how-to-setup-subdomain-or-host-multiple-domains-using-nginx-in-linux-server/>
<https://blog.logrocket.com/how-to-build-web-app-with-multiple-subdomains-nginx/>
<https://stackoverflow.com/questions/64955127/nginx-multiple-node-apps-with-multiple-subdomains>

- [X] Update Nginx to serve both sites
- [X] Serve Static Files
- [X] Update Endpoints to point to API
- [X] Rename `moving` to `box_packing`

FastAPI:

- [X] Tasks

## Config

- [X] maybe this should be settings
- [X] Need to split out the settings to separate classes and instantiate them in base class
- [X] pydantic `BaseSettings` class
- [X] Change the config to have different env files I think
- [X] Pydantic can get the env automatically so I don't have to do `environ.get('KEY')`
  - [X] Not applicable when using multiple .env files based on ENVIRONMENT env variable

## Move info to health check

- [ ] Move info
- [ ] Add server time
- [ ] Add local time
  - [ ] How do I do this?

## Change to localtime instead of server time

- [X] Pydantic Models?
  - [ ] No
- [X] SQLAlchemy models?
  - [ ] No
- [X] Migration most likely
  - [ ] No
- [X] Timezone cannot be displayed for all date ranges

## Add "notes" field to tasks

- [X] !! __MAKE NOTES__ !!
- [X] SQLAlchemy model
- [X] Pydantic model
- [X] Migration
- [X] Cut a release
  - I've decided that a release should include all of these related features
  - And it should be a tag on the main branch, instead of a release branch which gets deleted anyway

## Use Enum for task categories

- [X] <https://realpython.com/python-enum/>
- [X] <https://docs.python.org/3/library/enum.html>
- [X] Does Postgres support enum
  - Yes
- [X] SQLAlchemy model
- [X] Pydantic model
- [X] Migration
- [X] Make the tests take the new ENUM in the data generator
- [X] Cut a release
  - [X] Make notes

## 0.7.0 Rename entire project to ichrisbirch

FastAPI:

- [X] nginx files
- [X] supervisor files
- [X] folders
- [X] name of keys
- [X] name of security group
- [X] name of mongo servers
- [X] database names
- [X] Do a grep for all things euphoria

## Backups

- [X] Postgres
- [x] MongoDB
- [x] DynamoDB
- [X] Code
  - [X] Github

## Continuous Integration / Github Actions

Pre-commit Possibilites:

- [X] Black
- [X] Flake8
- [X] isort
- [X] bandit
- [X] Interrogate

- [X] shellcheck
- [X] <https://github.com/dosisod/refurb>
- [X] <https://github.com/asottile/pyupgrade>
- [X] <https://github.com/python/mypy>

- [N] Deploy action upon push of tags
  - [X] Actions
    - [N] Create GitHub release
    - [X] Deploy to ichrisbirch

## Upgrade to SQLAlchemy 2.0

- [X] [What's New in SQLAlchemy 2.0? - miguelgrinberg.com](https://blog.miguelgrinberg.com/post/what-s-new-in-sqlalchemy-2-0)
- [X] Upgrade in poetry
- [X] Check for syntax
