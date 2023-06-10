import logging
import os
import pathlib
from functools import lru_cache
from typing import Any, Optional, Union

import dotenv

logger = logging.getLogger(__name__)


class FlaskSettings:
    def __init__(self):
        self.SECRET_KEY: Optional[str] = os.getenv('SECRET_KEY')  # MUST be capitalized
        self.TESTING: Optional[bool] = bool(os.getenv('FLASK_TESTING'))
        self.DEBUG: Optional[bool] = bool(os.getenv('FLASK_DEBUG'))


class FastAPISettings:
    def __init__(self):
        self.host: Optional[str] = os.getenv('FASTAPI_HOST')
        self.port: Optional[str] = os.getenv('FASTAPI_PORT')
        self.title: str = 'iChrisBirch API'
        self.description: str = """## Backend API for iChrisBirch.com"""
        self.responses: dict[Union[int, str], dict[str, Any]] = {
            404: {'description': 'Not found'},
            403: {'description': 'Operation forbidden'},
        }


class PostgresSettings:
    def __init__(self):
        self.host: Optional[str] = os.getenv('POSTGRES_HOST')
        self.user: Optional[str] = os.getenv('POSTGRES_USER')
        self.password: Optional[str] = os.getenv('POSTGRES_PASSWORD')
        self.port: Optional[str] = os.getenv('POSTGRES_PORT')
        self.database: Optional[str] = os.getenv('POSTGRES_DB')

    @property
    def db_uri(self) -> str:
        return f'postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'


class SQLAlchemySettings:  # TODO: [2023/05/07] - This class is currently hardcoded to Postgres.
    def __init__(self):
        self.echo: bool = False
        self.track_modifications: bool = False
        self.host: Optional[str] = os.getenv('POSTGRES_HOST')
        self.user: Optional[str] = os.getenv('POSTGRES_USER')
        self.password: Optional[str] = os.getenv('POSTGRES_PASSWORD')
        self.port: Optional[str] = os.getenv('POSTGRES_PORT')
        self.database: Optional[str] = os.getenv('POSTGRES_DB')

    @property
    def db_uri(self) -> str:
        return f'postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'


class MongoDBSettings:
    def __init__(self):
        self.host: Optional[str] = os.getenv('MONGO_HOST')
        self.user: Optional[str] = os.getenv('MONGO_USER')
        self.password: Optional[str] = os.getenv('MONGO_PASSWORD')

    @property
    def db_uri(self) -> str:
        return f'mongodb://{self.user}:{self.password}@{self.host}'


class SQLiteSettings:
    def __init__(self):
        self.db_uri: Optional[str] = os.getenv('SQLITE_DATABASE_URI')


class LoggingSettings:
    def __init__(self):
        self.os_prefix: Optional[str] = os.getenv('OS_PREFIX')
        self.log_path: Optional[str] = os.getenv('LOG_PATH')
        self.log_format: Optional[str] = os.getenv('LOG_FORMAT')
        self.log_date_format: Optional[str] = os.getenv('LOG_DATE_FORMAT')
        self.log_level: Union[int, str] = os.getenv('LOG_LEVEL', logging.DEBUG)

    @property
    def log_dir(self) -> str:
        return str(self.os_prefix) + str(self.log_path)


class Settings:
    def __init__(self, env_file: pathlib.Path = pathlib.Path()):
        self.name: str = 'ichrisbirch'
        self.db_schemas: list[str] = ['apartments', 'box_packing', 'habits']
        self.api_url: Optional[str] = os.environ.get('API_URL')
        self.environment: Optional[str] = os.environ.get('ENVIRONMENT')
        self.os_prefix: Optional[str] = os.environ.get('OS_PREFIX')
        self.env_file: pathlib.Path = env_file
        self.request_timeout: int = 3

        self.flask = FlaskSettings()
        self.fastapi = FastAPISettings()
        self.postgres = PostgresSettings()
        self.sqlalchemy = SQLAlchemySettings()
        self.mongodb = MongoDBSettings()
        self.sqlite = SQLiteSettings()
        self.logging = LoggingSettings()


def load_environment(env_file: Optional[pathlib.Path | str] = None):
    if isinstance(env_file, pathlib.Path):
        logger.info(f'Loading Environment from pathlib.Path: {env_file}')
        if not env_file.exists():
            raise FileNotFoundError(f'Environment file not found: {env_file}')

    elif isinstance(env_file, str):
        logger.info(f'Loading Environment from string: {env_file}')
        if not pathlib.Path(env_file).exists():
            logger.warning(f'Environment file not found: {env_file}')
            match env_file:
                case 'development':
                    filename = '.dev.env'
                case 'testing':
                    filename = '.test.env'
                case 'production':
                    filename = '.prod.env'
                case _:
                    logger.error(f'Unrecognized Environment Selection: {env_file}')
                    raise ValueError(f'Unrecognized Environment Selection: {env_file}')
            logger.info(f'Loading environment variables from: {filename}')
            env_file = pathlib.Path(dotenv.find_dotenv(filename))
        else:
            logger.info(f'Loading environment variables from: {env_file}')
            env_file = pathlib.Path(env_file)

    else:
        logger.info(f'Loading Environment from ENVIRONMENT variable {env_file}')
        match ENV := os.getenv('ENVIRONMENT'):
            case 'development':
                filename = '.dev.env'
            case 'testing':
                filename = '.test.env'
            case 'production':
                filename = '.prod.env'
            case _:
                logger.error(f'Unrecognized ENVIRONMENT Variable: {ENV}. Check ENVIRONMENT is set.')
                raise ValueError(f'Unrecognized ENVIRONMENT Variable: {ENV}. Check ENVIRONMENT is set.')
        env_file = pathlib.Path(dotenv.find_dotenv(filename))

    logger.info(f'Loading environment variables from: {env_file}')
    dotenv.load_dotenv(env_file, override=True)
    return env_file


@lru_cache(maxsize=1)
def get_settings(env_file: Optional[pathlib.Path | str] = None) -> Settings:
    """Return settings based on Path, str, or ENVIRONMENT variable."""
    resolved_env_file = load_environment(env_file)
    return Settings(env_file=resolved_env_file)
