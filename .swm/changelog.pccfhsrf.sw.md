---
id: pccfhsrf
title: CHANGELOG
file_version: 1.1.3
app_version: 1.16.4
---

# Changelog

## Misc

*   Take code out of `__init__.py` files

    *   Put them in `main.py` for the module or name of module

    *   Import the names in the `__init__.py` file for better top level imports

*   Main Site Navigation

    *   Put this on base page that all pages inherit from

    *   Inherit CSS as well

*   Restructure site so that all apps are top level - \[X\] events - \[X\] countdowns - \[X\] journal - \[X\] habits

## v0.2.0 --> Move databases (Postgres, MongoDB, DynamoDB) to their own Servers

Prod only, further ahead will figure out how to sync dev and "testing" (god help me) to the prod environment

*   pg\_cron and update task priorities

*   MongoDB move to Atlas

## v0.3.0 --> Get rid of Flask-SQLAlchemy and Migrate Databases

*   Use regular SQLAlchemy instead.

*   Countdowns -> SQLAlchemy

*   Apartments -> MongoDB

    *   Skipping for now

*   Simplify Journal Entry MongoDB

*   Get rid of Events dict

    *   Maybe with Pydantic Models

## v0.4.0 --> Migrate Databases

*   Alembic

*   [https://alembic.sqlalchemy.org/en/latest/tutorial.html](https://alembic.sqlalchemy.org/en/latest/tutorial.html)

### v0.4.1 --> Hotfix: Add Stats to release

*   Output of tokei

*   Pytest with coverage

*   wily

*   Make it easy to add more in the future

## v0.5.0 --> FastAPI and Nginx

*   FastAPI Course

*   [https://academy.christophergs.com/courses/fastapi-for-busy-engineers/curriculum](https://academy.christophergs.com/courses/fastapi-for-busy-engineers/curriculum) API is being run on a different port/subdomain api.ichrisbirch.com [https://adamtheautomator.com/nginx-subdomain/](https://adamtheautomator.com/nginx-subdomain/) [https://hackprogramming.com/how-to-setup-subdomain-or-host-multiple-domains-using-nginx-in-linux-server/](https://hackprogramming.com/how-to-setup-subdomain-or-host-multiple-domains-using-nginx-in-linux-server/) [https://blog.logrocket.com/how-to-build-web-app-with-multiple-subdomains-nginx/](https://blog.logrocket.com/how-to-build-web-app-with-multiple-subdomains-nginx/) [https://stackoverflow.com/questions/64955127/nginx-multiple-node-apps-with-multiple-subdomains](https://stackoverflow.com/questions/64955127/nginx-multiple-node-apps-with-multiple-subdomains)

*   Update Nginx to serve both sites

*   Serve Static Files

*   Update Endpoints to point to API

*   Rename `moving` to `box_packing`

FastAPI:

*   Tasks

## Config

*   maybe this should be settings

*   Need to split out the settings to separate classes and instantiate them in base class

*   pydantic `BaseSettings` class

*   Change the config to have different env files I think

*   Pydantic can get the env automatically so I don't have to do `environ.get('KEY')`

    *   Not applicable when using multiple .env files based on ENVIRONMENT env variable

## Move info to health check

*   Move info

*   Add server time

*   Add local time

    *   How do I do this?

## Change to localtime instead of server time

*   Pydantic Models?

    *   No

*   SQLAlchemy models?

    *   No

*   Migration most likely

    *   No

*   Timezone cannot be displayed for all date ranges

## Add "notes" field to tasks

*   !! **MAKE NOTES** !!

*   SQLAlchemy model

*   Pydantic model

*   Migration

*   Cut a release

    *   I've decided that a release should include all of these related features

    *   And it should be a tag on the main branch, instead of a release branch which gets deleted anyway

## Use Enum for task categories

*   [https://realpython.com/python-enum/](https://realpython.com/python-enum/)

*   [https://docs.python.org/3/library/enum.html](https://docs.python.org/3/library/enum.html)

*   Does Postgres support enum

    *   Yes

*   SQLAlchemy model

*   Pydantic model

*   Migration

*   Make the tests take the new ENUM in the data generator

*   Cut a release

    *   Make notes

## 0.7.0 Rename entire project to ichrisbirch

FastAPI:

*   nginx files

*   supervisor files

*   folders

*   name of keys

*   name of security group

*   name of mongo servers

*   database names

*   Do a grep for all things euphoria

## Backups

*   Postgres

*   MongoDB

*   DynamoDB

*   Code

    *   Github

## Continuous Integration / Github Actions

Pre-commit Possibilities:

*   Black

*   Flake8

*   isort

*   bandit

*   Interrogate

*   shellcheck

*   [https://github.com/dosisod/refurb](https://github.com/dosisod/refurb)

*   [https://github.com/asottile/pyupgrade](https://github.com/asottile/pyupgrade)

*   [https://github.com/python/mypy](https://github.com/python/mypy)

*   \[N\] Deploy action upon push of tags

    *   Actions

        *   \[N\] Create GitHub release

        *   Deploy to ichrisbirch

## Upgrade to SQLAlchemy 2.0

*   [What's New in SQLAlchemy 2.0? - miguelgrinberg.com](https://blog.miguelgrinberg.com/post/what-s-new-in-sqlalchemy-2-0)

*   Upgrade in poetry

*   Check for syntax

## Tasks Upgrades

*   CHANGE: form to crud

*   REMOVE: the Fake Tasks and Delete Tasks

    *   Make sure data generator for tests captures the logic

*   Chart.js

*   [https://blog.ruanbekker.com/blog/2017/12/14/graphing-pretty-charts-with-python-flask-and-chartjs/](https://blog.ruanbekker.com/blog/2017/12/14/graphing-pretty-charts-with-python-flask-and-chartjs/)

*   CHANGE: the priority subtraction to daily

### `tasks.py /all`

*   ADD: SEARCH capability!

*   ADD: `Complete` button for all tasks

    *   Should be for all of the tasks after the first 5

    *   Sometimes tasks get completed early and they need to be marked as complete before in the top 5

    *   Similar to the delete button

*   ADD: filtering of `All | Completed | Not Completed` tasks.

    *   Sort options as well?

*   ADD: Delete button for all tasks.

    *   Sometimes a task is added in error and needs to be deleted

*   CHANGE: Have `add task` redirect to the page that it was called from, instead of the priorities page.

    *   Example in apartments endpoint

### Add categories to tasks ENUM

*   Compare this with the initial adding of the ENUM

    *   Purchase

    *   Work

    *   Kitchen

## Create /autotask endpoint

*   Simple storage of chores that need to be added to the priority list

    *   Columns

        *   Same as \[tasks\] columns

        *   Additionally:

            *   Add date for autochore

            *   How often to add it (days)

*   routes/autotask.py

*   endpoints/autotask.py

*   crud/autotask.py

*   static/css/autotask.scss

*   templates/autotasks/\*

*   Add to base.html navigation

*   tests/endpoints/test\_autotasks.py

### Miscellaneous Upgrades and Features

*   Fix CSS autotask boxes (quickly)

*   AutoTask - Add columns

    *   `first_run_date`

    *   `run_count`

*   Alembic upgrade prod

*   `main.py` files should be `home.py` files in app and api

*   `euphoria_ddl.sql`

*   `.flake8` does this not work with pyproject?

    *   Docs if it does not

## Add Countdowns to API routes

*   Add ALLLL

<br/>

This file was generated by Swimm. [Click here to view it in the app](https://app.swimm.io/repos/Z2l0aHViJTNBJTNBaWNocmlzYmlyY2glM0ElM0FkYXRhcG9pbnRjaHJpcw==/docs/pccfhsrf).
