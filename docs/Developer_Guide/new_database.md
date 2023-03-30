# Setup a New Postgres Database

## Schemas

SQLAlchemy cannot create the schemas, neither can alembic, have to create them manually first time
`create-schemas.py` to add the schemas

## Alembic

Run in `ichrisbirch`

Create the initial tables from the SQLAlchemy models (purpose of --autogenerate)
`alembic revision --autogenerate -m 'init_tables'`

Run the upgrade to actually create the tables
`alembic upgrade head`