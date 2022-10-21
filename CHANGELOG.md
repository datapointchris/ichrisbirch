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



# v0.2.0 --> Move databases (Postgres, MongoDB, DynamoDB) to their own Servers
---
Prod only, further ahead will figure out how to sync dev and "testing" (god help me) to the prod environment
- [X] pg_cron and update task priorities
- [X] MongoDB move to Atlas



# v0.3.0 --> Get rid of Flask-SQLAlchemy and Migrate Databases
- [X] Use regular SQLAlchemy instead.
- [X] Countdowns -> SQLAlchemy
- [ ] Apartments -> MongoDB
  - [ ] Skipping for now
- [X] Simplify Journal Entry MongoDB
- [X] Get rid of Events dict
  - [X] Maybe with Pydantic Models



# v0.4.0 --> Migrate Databases
- [X] Alembic
- [X] https://alembic.sqlalchemy.org/en/latest/tutorial.html



# v0.4.1 --> Hotfix: Add Stats to release
- [X] Output of tokei
- [X] Pytest with coverage
- [X] wily
- [X] Make it easy to add more in the future



# v0.5.0 --> FastAPI and Nginx
- FastAPI Course
- [X] https://academy.christophergs.com/courses/fastapi-for-busy-engineers/curriculum
API is being run on a different port/subdomain
api.ichrisbirch.com
https://adamtheautomator.com/nginx-subdomain/
https://hackprogramming.com/how-to-setup-subdomain-or-host-multiple-domains-using-nginx-in-linux-server/
https://blog.logrocket.com/how-to-build-web-app-with-multiple-subdomains-nginx/
https://stackoverflow.com/questions/64955127/nginx-multiple-node-apps-with-multiple-subdomains

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