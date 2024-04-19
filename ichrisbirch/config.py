import functools
import logging
import os
import pathlib
from typing import Optional

import dotenv

logger = logging.getLogger(__name__)


class FlaskSettings:
    def __init__(self):
        self.host: Optional[str] = os.getenv('FLASK_HOST')
        self.port: Optional[str] = os.getenv('FLASK_PORT')
        self.SECRET_KEY: Optional[str] = os.getenv('FLASK_SECRET_KEY')  # MUST be capitalized
        self.TESTING: Optional[bool] = bool(os.getenv('FLASK_TESTING'))
        self.DEBUG: Optional[bool] = bool(os.getenv('FLASK_DEBUG'))


class FastAPISettings:
    def __init__(self):
        self.host: Optional[str] = os.getenv('FASTAPI_HOST')
        self.port: Optional[str] = os.getenv('FASTAPI_PORT')
        self.title: str = 'iChrisBirch API'
        self.description: str = """## Backend API for iChrisBirch.com"""


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


class SQLAlchemySettings:
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


class PlaywrightSettings:
    def __init__(self):
        self.timeout = 2_000


class GithubSettings:
    def __init__(self):
        self.api_token: Optional[str] = os.getenv('GITHUB_API_TOKEN')
        self.api_url_issues: str = 'https://api.github.com/repos/datapointchris/ichrisbirch/issues'
        self.api_url_labels: str = 'https://api.github.com/repos/datapointchris/ichrisbirch/labels'
        self.api_headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {self.api_token}',
            'X-GitHub-Api-Version': '2022-11-28',
        }


class Settings:
    def __init__(self, env_file: pathlib.Path = pathlib.Path()):
        self.NAME: str = 'ichrisbirch'
        self.DB_SCHEMAS: list[str] = ['apartments', 'box_packing', 'habits']
        self.ENVIRONMENT: Optional[str] = os.environ.get('ENVIRONMENT')
        self.ENV_FILE: pathlib.Path = env_file
        self.REQUEST_TIMEOUT: int = 3

        self.flask = FlaskSettings()
        self.fastapi = FastAPISettings()
        self.postgres = PostgresSettings()
        self.sqlalchemy = SQLAlchemySettings()
        self.mongodb = MongoDBSettings()
        self.sqlite = SQLiteSettings()
        self.playwright = PlaywrightSettings()
        self.github = GithubSettings()

    @property
    def api_url(self) -> str:
        return f'http://{self.fastapi.host}:{self.fastapi.port}'


def load_environment(env_file: Optional[pathlib.Path | str] = None):
    if isinstance(env_file, pathlib.Path):
        logger.info(f'Loading Environment from pathlib.Path: {env_file}')
        if not env_file.exists():
            raise FileNotFoundError(f'Environment pathlib.Path not found: {env_file}')

    elif isinstance(env_file, str):
        logger.info(f'Loading Environment from string: {env_file}')
        if not pathlib.Path(env_file).exists():
            match env_file:
                case 'development':
                    filename = '.dev.env'
                case 'testing':
                    filename = '.test.env'
                case 'production':
                    filename = '.prod.env'
                case _:
                    error_msg = f'Unrecognized Environment Selection: {env_file}'
                    logger.error(error_msg)
                    raise ValueError(error_msg)
            logger.info(f'Loading environment variables from: {filename}')
            env_file = pathlib.Path(dotenv.find_dotenv(filename))
        else:
            logger.info(f'Loading environment variables from: {env_file}')
            env_file = pathlib.Path(env_file)

    else:
        logger.info(f'Loading environment: {os.getenv("ENVIRONMENT")}')
        match ENV := os.getenv('ENVIRONMENT'):
            case 'development':
                filename = '.dev.env'
            case 'testing':
                filename = '.test.env'
            case 'production':
                filename = '.prod.env'
            case _:
                error_msg = f'Unrecognized ENVIRONMENT Variable: {ENV}. Check ENVIRONMENT is set.'
                logger.error(error_msg)
                raise ValueError(error_msg)
        env_file = pathlib.Path(dotenv.find_dotenv(filename))

    logger.info(f'Env file: {env_file}')
    dotenv.load_dotenv(env_file, override=True)
    return env_file


@functools.lru_cache(maxsize=1)
def get_settings(env_file: Optional[pathlib.Path | str] = None) -> Settings:
    """Return settings based on Path, str, or ENVIRONMENT variable."""
    resolved_env_file = load_environment(env_file)
    return Settings(env_file=resolved_env_file)
