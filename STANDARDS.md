# Standards
===========
Sardonic:
- disdainfully or skeptically humorous; derisively mocking

## Style Guide
==============
https://github.com/google/styleguide/blob/gh-pages/pyguide.md



## SQL STYLING
==============
https://github.com/dbt-labs/corp/blob/main/dbt_style_guide.md
https://gist.github.com/fredbenenson/7bb92718e19138c20591


## Naming
=========
### Column Names
    Booleans - should start with an “is_” , “has_” or ““ and should always been a “True” or “False” value and not “Y” or “N'“ or other variants.
    Dates - should end in “_date”
    Timestamps -- should end with “_ts”

### Environment Specific Files
    {env.project.resource.}


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
`feature:` Feature work
`wip:` Work in progress, checkpoint
`test:` Add, modify, refactor tests
`refactor:` Rewrite/restructure your code, however does not change any behavior
`bugfix:` Fix a bug
`performance:` Refactor to improve performance
`style:` Code style, lint or formatting
`docs:` Documentation
`build:` Build components like build tool, ci pipeline, dependencies, project version
`ops:` Operational components like infrastructure, deployment, backup, recovery
`chore:` Miscellaneous commits e.g. modifying .gitignore moving or renaming files or directories

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


