import functools
import logging
import os
import pathlib
from datetime import timedelta
from typing import Optional

import dotenv

logger = logging.getLogger(__name__)


class AWSSettings:
    def __init__(self):
        self.region: str = os.environ['AWS_REGION']
        self.account_id: str = os.environ['AWS_ACCOUNT_ID']
        self.kms_key: str = os.environ['AWS_KMS_KEY']
        self.postgres_backup_role: str = 'role/S3DatabaseBackups'
        self.s3_backup_bucket: str = 'ichrisbirch-backups'


class FastAPISettings:
    def __init__(self):
        self.host: str = os.environ['FASTAPI_HOST']
        self.port: str = os.environ['FASTAPI_PORT']
        self.title: str = 'iChrisBirch API'
        self.description: str = """## Backend API for iChrisBirch.com"""


class FlaskSettings:
    def __init__(self):
        self.host: str = os.environ['FLASK_HOST']
        self.port: str = os.environ['FLASK_PORT']
        self.SECRET_KEY: str = os.environ['FLASK_SECRET_KEY']  # MUST be capitalized
        self.TESTING: bool = bool(os.environ['FLASK_TESTING'])
        self.DEBUG: bool = bool(os.environ['FLASK_DEBUG'])


class FlaskLoginSettings:
    def __init__(self):
        self.login_view: str = 'auth.login'
        self.login_message: str = 'Please log in to access this page.'
        self.login_message_category: str = 'info'
        self.REMEMBER_COOKIE_DURATION: timedelta = timedelta(days=1)
        self.REMEMBER_COOKIE_DOMAIN: str = 'ichrisbirch.com'
        self.SESSION_PROTECTION: str = 'strong'


class GithubSettings:
    def __init__(self):
        self.api_token: str = os.environ['GITHUB_API_TOKEN']
        self.api_url_issues: str = 'https://api.github.com/repos/datapointchris/ichrisbirch/issues'
        self.api_url_labels: str = 'https://api.github.com/repos/datapointchris/ichrisbirch/labels'
        self.api_headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {self.api_token}',
            'X-GitHub-Api-Version': '2022-11-28',
        }


class MongoDBSettings:
    def __init__(self):
        self.host: str = os.environ['MONGO_HOST']
        self.user: str = os.environ['MONGO_USER']
        self.password: str = os.environ['MONGO_PASSWORD']

    @property
    def db_uri(self) -> str:
        return f'mongodb://{self.user}:{self.password}@{self.host}'


class PlaywrightSettings:
    def __init__(self):
        self.timeout = 5_000


class PostgresSettings:
    def __init__(self):
        self.host: str = os.environ['POSTGRES_HOST']
        self.user: str = os.environ['POSTGRES_USER']
        self.password: str = os.environ['POSTGRES_PASSWORD']
        self.port: str = os.environ['POSTGRES_PORT']
        self.database: str = os.environ['POSTGRES_DB']

    @property
    def db_uri(self) -> str:
        return f'postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'


class SQLAlchemySettings:
    def __init__(self):
        self.echo: bool = False
        self.track_modifications: bool = False
        self.host: str = os.environ['POSTGRES_HOST']
        self.user: str = os.environ['POSTGRES_USER']
        self.password: str = os.environ['POSTGRES_PASSWORD']
        self.port: str = os.environ['POSTGRES_PORT']
        self.database: str = os.environ['POSTGRES_DB']

    @property
    def db_uri(self) -> str:
        return f'postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'


class SQLiteSettings:
    def __init__(self):
        self.db_uri: str = os.environ['SQLITE_DATABASE_URI']


class Settings:
    def __init__(self, env_file: pathlib.Path = pathlib.Path()):
        self.NAME: str = 'ichrisbirch'
        self.DB_SCHEMAS: list[str] = ['apartments', 'box_packing', 'habits']
        self.ENVIRONMENT: str = os.environ['ENVIRONMENT']
        self.ENV_FILE: pathlib.Path = env_file
        self.REQUEST_TIMEOUT: int = 3

        self.aws = AWSSettings()
        self.fastapi = FastAPISettings()
        self.flask = FlaskSettings()
        self.flasklogin = FlaskLoginSettings()
        self.github = GithubSettings()
        self.mongodb = MongoDBSettings()
        self.playwright = PlaywrightSettings()
        self.postgres = PostgresSettings()
        self.sqlalchemy = SQLAlchemySettings()
        self.sqlite = SQLiteSettings()

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
        logger.info(f'Loading environment: {os.environ["ENVIRONMENT"]}')
        match (ENV := os.environ['ENVIRONMENT']):
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
