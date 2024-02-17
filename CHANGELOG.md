# Changelog

## Misc

- [X] Take code out of `__init__.py` files
  - [X] Put them in `main.py` for the module or name of module
  - [X] Import the names in the `__init__.py` file for better top level imports
- [X] Main Site Navigation
  - [X] Put this on base page that all pages inherit from
  - [X] Inherit CSS as well
- [X] Restructure site so that all apps are top level
      - [X] events
      - [X] countdowns
      - [X] journal
      - [X] habits

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

Pre-commit Possibilities:

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

## Tasks Upgrades

- [X] CHANGE: form to crud
- [X] REMOVE: the Fake Tasks and Delete Tasks
  - [X] Make sure data generator for tests captures the logic
- [X] Chart.js
- [X] <https://blog.ruanbekker.com/blog/2017/12/14/graphing-pretty-charts-with-python-flask-and-chartjs/>
- [X] CHANGE: the priority subtraction to daily

### `tasks.py /all`

- [X] ADD: SEARCH capability!
- [X] ADD: `Complete` button for all tasks
  - Should be for all of the tasks after the first 5
  - Sometimes tasks get completed early and they need to be marked as complete before in the top 5
  - Similar to the delete button
- [X] ADD: filtering of `All | Completed | Not Completed` tasks.
  - Sort options as well?
- [X] ADD: Delete button for all tasks.  
  - Sometimes a task is added in error and needs to be deleted
- [X] CHANGE: Have `add task` redirect to the page that it was called from, instead of the priorities page.
  - Example in apartments endpoint

### Add categories to tasks ENUM

- [X] Compare this with the initial adding of the ENUM
  - [X] Purchase
  - [X] Work
  - [X] Kitchen

## Create /autotask endpoint

- [X] Simple storage of chores that need to be added to the priority list
  - [X] Columns
    - Same as [tasks] columns
    - Additionally:
      - Add date for autochore
      - How often to add it (days)
- [X] routes/autotask.py
- [X] endpoints/autotask.py
- [X] crud/autotask.py
- [X] static/css/autotask.scss
- [X] templates/autotasks/*
- [X] Add to base.html navigation
- [X] tests/endpoints/test_autotasks.py

### Miscellaneous Upgrades and Features

- [X] Fix CSS autotask boxes (quickly)
- [X] AutoTask - Add columns
  - [X] `first_run_date`
  - [X] `run_count`
- [X] Alembic upgrade prod
- [X] `main.py` files should be `home.py` files in app and api
- [X] `euphoria_ddl.sql`
- [X] `.flake8` does this not work with pyproject?
  - [X] Docs if it does not

## Add Countdowns to API routes

- [X] Add ALLLL

## Autotasks

- [X] Always run the new autotask right now
- [X] Test to see if the autotask creator actually works
- [X] Check on the daily subtraction
  - [X] This should be in the logs
  - [X] Move to airflow eventually
    - [X] Decided to go with APScheduler instead, so it is self contained

- [X] `from http import HTTPStatus`
  - [X] fastapi `status` is much better, more descriptive and returns a constant that the IDE can see.

- [X] Replace requests with httpx

## CSS files

- [X] Need to have reset
- [X] [mkdocs-material/_resets.scss at master · squidfunk/mkdocs-material · GitHub](https://github.com/squidfunk/mkdocs-material/blob/master/src/assets/stylesheets/main/_resets.scss)
