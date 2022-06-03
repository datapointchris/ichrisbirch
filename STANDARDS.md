# Standards
=========


## API
======
There are many HTTP methods, but the most important ones are:
POST for creating resources
POST /users
GET for reading resources (both single resources and collections)
GET /users
GET /users/{id}
PATCH for applying partial updates to a resource
PATCH /users/{id}
PUT for applying full updates to a resource (replaces the current resource)
PUT /users/{id}
DELETE for deleting resources
DELETE /users/{id}


## Git
======
### Branching
`{app_name}-{purpose-of-branch}

### Commits
Conventional Commits
https://gist.github.com/qoomon/5dfcdf8eec66a051ecd85625518cfd13
`feat:` that adds a new feature
`fix:` that fixes a bug
`refactor:` that rewrite/restructure your code, however does not change any behaviour
`perf:`are special refactor commits, that improve performance
`style:` that do not affect the meaning (white-space, formatting, missing semi-colons, etc)
`test:` that add missing tests or correcting existing tests
`docs:` that affect documentation only
`build:` that affect build components like build tool, ci pipeline, dependencies, project version, ...
`ops:` that affect operational components like infrastructure, deployment, backup, recovery, ...
`chore:` Miscellaneous commits e.g. modifying .gitignore

### Issues and Milestones
TBD
Each milestone is a new minor version


## Versioning
=============
SemVer
https://semver.org


## CSS
======
BEM


## Technologies
===============
Python 3.10.1  
Postgres 14.2  
DynamoDB
MongoDB