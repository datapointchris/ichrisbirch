# Adding A New Application

For this document example we will be creating a new app called `Items`

|                                      |           |
| ------------------------------------ | --------- |
| :material-database: db table         | `items`   |
| :simple-sqlalchemy: sqlalchemy model | `Item`    |
| :simple-pydantic: pydantic schema    | `Item`    |
| :material-application: app endpoint  | `/items`  |
| :material-api: api endpoint          | `/items/` |

## Sqlalchemy Model

:material-import: Import new models into `ichrisbirch/alembic/env.py`  

:material-import: Import new models into `ichrisbirch/models/__init__.py`  
For easy reference from the module level.

```python
from ichrisbirch import models

item = models.Item(**data)
```

## Pydantic Schema

:material-import: Import new schemas into `ichrisbirch/schemas/__init__.py`  
For easy reference from the module level.

```python
from ichrisbirch import schemas

item = schemas.ItemCreate(**data)
```

## Application Blueprint

### App Routes

## Application Blueprint to App Factory

## API Router

### API Endpoints

:material-import: Import in `ichrisbirch/schemas/__init__.py`  
For easy reference from the module level.

## API Router to API Factory

## HTML base.html and index.html

## Navigation Link

:link: Add link to navigation in `ichrisbirch/app/templates/base.html`

## Stylesheet

## Tests

### Testing Data

:material-test: Add testing data into `tests/testing_data`  
:material-import: Import the test data in `tests/testing_data/__init__.py`
:material-plus: Add testing data to `tests/conftest.py/get_test_data()`

### API Endpoints Tests

### App Routes Tests

## Frontend Tests
