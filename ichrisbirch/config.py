import importlib.metadata
import os
from functools import lru_cache
from typing import Any, Optional, Union

import dotenv
from pydantic import BaseSettings, Field, MongoDsn, PostgresDsn


class FlaskSettings(BaseSettings):
    """Config settings for Flask"""

    # https://flask.palletsprojects.com/en/latest/api/#sessions
    SECRET_KEY: str


class FastAPISettings(BaseSettings):
    """Config settings for FastAPI"""

    title: str = 'iChrisBirch API'
    description: str = """## With all the fixins"""
    responses: dict[Union[int, str], dict[str, Any]] = Field(
        default_factory=lambda: {
            404: {'description': 'Not found'},
            403: {"description": "Operation forbidden"},
        }
    )


class PostgresSettings(BaseSettings):
    """Config settings for Postgres"""

    host: str = Field(env='POSTGRES_HOST')
    user: str = Field(env='POSTGRES_USER')
    password: str = Field(env='POSTGRES_PASSWORD', secret=True)
    port: str = '5432'
    database: str = 'ichrisbirch'

    @property
    def db_uri(self) -> str:
        return str(
            PostgresDsn.build(
                scheme='postgresql',
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                path=f'/{self.database}',
            )
        )


class SQLAlchemySettings(BaseSettings):
    """Config settings for SQLAlchemy"""

    # TODO: [2023/05/07] - This class is currently hardcoded to Postgres.
    echo: bool = False
    track_modifications: bool = False

    host: str = Field(env='POSTGRES_HOST')
    user: str = Field(env='POSTGRES_USER')
    password: str = Field(env='POSTGRES_PASSWORD', secret=True)
    port: str = '5432'
    database: str = 'ichrisbirch'

    @property
    def db_uri(self) -> str:
        return str(
            PostgresDsn.build(
                scheme='postgresql',
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                path=f'/{self.database}',
            )
        )


class MongoDBSettings(BaseSettings):
    """Config settings for MongoDB"""

    host: str = Field(env='MONGO_HOST')
    user: str = Field(env='MONGO_USER')
    password: str = Field(env='MONGO_PASSWORD', secret=True)

    @property
    def db_uri(self) -> str:
        return str(
            MongoDsn.build(
                scheme='mongodb',
                host=self.host,
                user=self.user,
                password=self.password,
            )
        )


class SQLiteSettings(BaseSettings):
    """Config settings for SQLite"""

    db_uri: str = Field(env='SQLITE_DATABASE_URI')


class LoggingSettings(BaseSettings):
    """Config settings for Logging"""

    os_prefix: str
    log_path: str
    log_format: str
    log_date_format: str
    log_level: Union[int, str] = Field('DEBUG', env='LOG_LEVEL')

    @property
    def log_dir(self) -> str:
        return self.os_prefix + self.log_path


class Settings(BaseSettings):
    """Base settings class that contains all other settings.

    Order of Operations:
    1. import `get_settings` into a module
        1a. This runs the code in this file
        1b. __post_init__ is used to only set values after class is instantiated, instead of when code is run
    2. call `get_settings` to get the settings object
        2a. Load the environment variables from:
            - env_file passed in
            - .env file based on `ENVIRONMENT` variable
        2b. run __post_init__ to instantiate the classes that depend on environment variables

    *** Thoughts ***
    I'm not sure this is better than having a DevelopmentSettings, TestingSettings, and ProductionSettings classes
    with a factory function that returns the correct class based on the `ENVIRONMENT` variable.


    *** Notes ***
    Since pydantic automatically converts environment variables to their corresponding data types,
    we don't need to use Optional or Union in our Field definitions anymore.

    """

    name: str = 'ichrisbirch'
    version: str = Field(importlib.metadata.version(name))
    db_schemas: list[str] = Field(default_factory=lambda: ['apartments', 'box_packing', 'habits'])
    api_url: str
    environment: str
    os_prefix: str
    request_timeout: int = 3

    flask: FlaskSettings
    fastapi: FastAPISettings
    sqlite: SQLiteSettings
    mongodb: MongoDBSettings
    postgres: PostgresSettings
    sqlalchemy: SQLAlchemySettings
    logging: LoggingSettings


@lru_cache()
def get_settings(env_file: Optional[str] = None) -> Settings:
    if not env_file:
        match ENV := os.getenv('ENVIRONMENT'):
            case 'development':
                env_file = dotenv.find_dotenv('.dev.env')
            case 'testing':
                env_file = dotenv.find_dotenv('.test.env')
            case 'production':
                env_file = dotenv.find_dotenv('.prod.env')
            case _:
                raise ValueError(
                    f'Unrecognized Environment Variable: {ENV}\n' 'Did you set ENVIRONMENT before starting the program?'
                )
    dotenv.load_dotenv(env_file)
    # TODO: [2023/05/08] - Workaround for instatiation errors:
    # E pydantic.error_wrappers.ValidationError: 7 validation errors for Settings
    # E flask field required (type=value_error.missing)
    return Settings(
        flask=FlaskSettings(),
        fastapi=FastAPISettings(),
        sqlite=SQLiteSettings(),
        mongodb=MongoDBSettings(),
        postgres=PostgresSettings(),
        sqlalchemy=SQLAlchemySettings(),
        logging=LoggingSettings(),
    )  # type: ignore
