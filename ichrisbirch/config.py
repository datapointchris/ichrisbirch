import importlib.metadata
import os
from functools import lru_cache
from typing import Any, Optional, Union

import dotenv
from pydantic import BaseSettings, Field, MongoDsn, PostgresDsn, SecretStr, validator

ENV: Optional[str] = os.getenv('ENVIRONMENT')

match ENV:
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
# Must load the .env file first since settings is instantiated last
dotenv.load_dotenv(env_file)


class FlaskSettings(BaseSettings):
    """Config settings for Flask"""

    # https://flask.palletsprojects.com/en/latest/api/#sessions
    secret_key: SecretStr
    env: Optional[str] = ENV


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
                scheme='postgresql://',
                host=self.host,
                user=self.user,
                password=self.password,
                port=self.port,
                database=self.database,
            )
        )


class SQLAlchemySettings(BaseSettings):
    """Config settings for SQLAlchemy"""

    echo: bool = False
    track_modifications: bool = False
    db_uri: str = ""

    @validator('db_uri')
    def db_uri_validator(cls, value: str) -> str:
        """
        The check `if '?' not in value` ensures that the query parameter is only added to the URI
        if it doesn't already contain a query string.
        If the URI already has a query string,
        adding another query parameter with a `?` would create a syntax error in the URI.

        In the case of SQLite, the `check_same_thread` parameter is only relevant for connections
        that are used within the same thread that they were created.
        If the URI already contains a query string it is assumed that the application code
        has already included any necessary query parameters
        and the validator doesn't add the `check_same_thread` parameter again.
        """

        if 'sqlite' in value and '?' not in value:
            value += '?check_same_thread=False'
        return value


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

    log_path: str = f"{os.getenv('OS_PREFIX')}{os.getenv('LOG_PATH')}"
    log_format: str
    log_date_format: str
    log_level: Union[int, str] = Field('DEBUG', env='LOG_LEVEL')


class Settings(BaseSettings):
    """Base settings class that contains all other settings.

    In the Config class, we're setting the env_file based on the ENVIRONMENT variable.
    If ENVIRONMENT is not recognized, env_file will be None.
    When env_file is set, pydantic will automatically try to load the variables from the specified file.

    Also note that since pydantic automatically converts environment variables to their corresponding data types,
    we don't need to use Optional or Union in our Field definitions anymore.

    """

    name: str = 'ichrisbirch'
    version: str = Field(importlib.metadata.version(name))
    db_schemas: list[str] = Field(default_factory=lambda: ['apartments', 'box_packing', 'habits'])
    api_url: str
    environment: str
    os_prefix: str
    request_timeout: int = 3

    flask = FlaskSettings()
    fastapi = FastAPISettings()
    sqlite = SQLiteSettings()
    mongodb = MongoDBSettings()
    postgres = PostgresSettings()
    sqlalchemy = SQLAlchemySettings()
    logging = LoggingSettings()
    sqlalchemy.db_uri = postgres.db_uri

    class Config:
        env_file = env_file


@lru_cache()
def get_settings():
    return Settings()


settings = Settings()
