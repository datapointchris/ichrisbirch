import os
from dataclasses import dataclass, field
from typing import Any, Union

from ichrisbirch import __version__


@dataclass
class FlaskSettings:
    """Config settings for Flask"""

    SECRET_KEY: str | None = os.getenv('SECRET_KEY')
    ENV: str | None = os.getenv('ENVIRONMENT')


@dataclass
class FastAPISettings:
    """Config settings for FastAPI"""

    TITLE: str = 'iChrisBirch API'
    DESCRIPTION: str = """## With all the fixins"""
    RESPONSES: dict[Union[int, str], dict[str, Any]] = field(
        default_factory=lambda: {
            404: {'description': 'Not found'},
            403: {"description": "Operation forbidden"},
        }
    )


@dataclass
class PostgresSettings:
    """Config settings for Postgres"""

    POSTGRES_URI: str | None = os.getenv('POSTGRES_URI')
    POSTGRES_USER: str | None = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD: str | None = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_DATABASE_URI: str = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_URI}:5432/ichrisbirch'


@dataclass
class SQLAlchemySettings:
    """Config settings for SQLAlchemy"""

    SQLALCHEMY_ECHO: bool = True
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_DATABASE_URI: str = ""


@dataclass
class MongoDBSettings:
    """Config settings for MongoDB"""

    MONGODB_URI: str | None = os.getenv('MONGODB_URI')
    MONGODB_USER: str | None = os.getenv('MONGODB_USER')
    MONGODB_PASSWORD: str | None = os.getenv('MONGODB_PASSWORD')
    MONGODB_DATABASE_URI: str = (
        f'mongodb+srv://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_URI}/ichrisbirch?retryWrites=true&w=majority'
    )


@dataclass
class DynamoDBSettings:
    """Config settings for DynamoDB"""

    DYNAMODB_URL: str | None = os.getenv('DYNAMODB_URL')
    DYNAMODB_USER: str | None = os.getenv('DYNAMODB_USER')
    DYNAMODB_PASSWORD: str | None = os.getenv('DYNAMODB_PASSWORD')
    DYNAMODB_DATABASE_URI: str | None = os.getenv('DYNAMODB_DATABASE_URI')


@dataclass
class SQLiteSettings:
    """Config settings for SQLite"""

    SQLITE_DATABASE_URI: str | None = os.getenv('SQLITE_DATABASE_URI')


@dataclass
class LoggingSettings:
    """Config settings for Logging"""

    LOG_PATH: str | None = f"{os.getenv('OS_PREFIX')}{os.getenv('LOG_PATH')}"
    LOG_FORMAT: str | None = os.getenv('LOG_FORMAT')
    LOG_LEVEL: Union[int, str] = os.getenv('LOG_LEVEL', 'DEBUG')


@dataclass
class Settings:
    """Base settings class that contains all other settings."""

    NAME: str = 'ichrisbirch.com'
    VERSION: str = __version__
    DB_SCHEMAS: list[str] = field(default_factory=lambda: ['apartments', 'box_packing', 'habits'])
    API_URL: str | None = os.getenv('API_URL')
    ENVIRONMENT: str | None = os.getenv('ENVIRONMENT')
    OS_PREFIX: str | None = os.getenv('OS_PREFIX')

    flask = FlaskSettings()
    fastapi = FastAPISettings()
    sqlite = SQLiteSettings()
    mongodb = MongoDBSettings()
    dynamodb = DynamoDBSettings()
    postgres = PostgresSettings()
    sqlalchemy = SQLAlchemySettings()
    logging = LoggingSettings()
    sqlalchemy.SQLALCHEMY_DATABASE_URI = postgres.POSTGRES_DATABASE_URI
