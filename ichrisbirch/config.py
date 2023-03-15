import importlib.metadata
import os
from dataclasses import dataclass, field
from typing import Any, Optional, Union

import dotenv

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
dotenv.load_dotenv(env_file)


@dataclass
class FlaskSettings:
    """Config settings for Flask"""

    SECRET_KEY: Optional[str] = os.getenv('SECRET_KEY')
    ENV: Optional[str] = os.getenv('ENVIRONMENT')


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

    POSTGRES_URI: Optional[str] = os.getenv('POSTGRES_URI')
    POSTGRES_USER: Optional[str] = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD: Optional[str] = os.getenv('POSTGRES_PASSWORD')
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

    MONGODB_URI: Optional[str] = os.getenv('MONGODB_URI')
    MONGODB_USER: Optional[str] = os.getenv('MONGODB_USER')
    MONGODB_PASSWORD: Optional[str] = os.getenv('MONGODB_PASSWORD')
    MONGODB_DATABASE_URI: str = (
        f'mongodb+srv://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_URI}/ichrisbirch?retryWrites=true&w=majority'
    )


@dataclass
class DynamoDBSettings:
    """Config settings for DynamoDB"""

    DYNAMODB_URL: Optional[str] = os.getenv('DYNAMODB_URL')
    DYNAMODB_USER: Optional[str] = os.getenv('DYNAMODB_USER')
    DYNAMODB_PASSWORD: Optional[str] = os.getenv('DYNAMODB_PASSWORD')
    DYNAMODB_DATABASE_URI: Optional[str] = os.getenv('DYNAMODB_DATABASE_URI')


@dataclass
class SQLiteSettings:
    """Config settings for SQLite"""

    SQLITE_DATABASE_URI: Optional[str] = os.getenv('SQLITE_DATABASE_URI')


@dataclass
class LoggingSettings:
    """Config settings for Logging"""

    LOG_PATH: Optional[str] = f"{os.getenv('OS_PREFIX')}{os.getenv('LOG_PATH')}"
    LOG_FORMAT: Optional[str] = os.getenv('LOG_FORMAT')
    LOG_DATE_FORMAT: Optional[str] = os.getenv('LOG_DATE_FORMAT')
    LOG_LEVEL: Union[int, str] = os.getenv('LOG_LEVEL', 'DEBUG')


@dataclass
class Settings:
    """Base settings class that contains all other settings."""

    NAME: str = 'ichrisbirch'
    VERSION: str = importlib.metadata.version(NAME)
    DB_SCHEMAS: list[str] = field(default_factory=lambda: ['apartments', 'box_packing', 'habits'])
    API_URL: Optional[str] = os.getenv('API_URL')
    ENVIRONMENT: Optional[str] = os.getenv('ENVIRONMENT')
    OS_PREFIX: Optional[str] = os.getenv('OS_PREFIX')
    REQUEST_TIMEOUT: int = 3

    flask = FlaskSettings()
    fastapi = FastAPISettings()
    sqlite = SQLiteSettings()
    mongodb = MongoDBSettings()
    dynamodb = DynamoDBSettings()
    postgres = PostgresSettings()
    sqlalchemy = SQLAlchemySettings()
    logging = LoggingSettings()
    sqlalchemy.SQLALCHEMY_DATABASE_URI = postgres.POSTGRES_DATABASE_URI


settings = Settings()
