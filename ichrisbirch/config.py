import functools
import logging
import os
from datetime import timedelta

import boto3
import dotenv

from ichrisbirch.util import find_project_root
from ichrisbirch.util import log_caller

logger = logging.getLogger(__name__)


class AISettings:
    class OpenAISettings:
        def __init__(self) -> None:
            self.api_key: str = os.environ['AI_OPENAI_API_KEY']
            self.model = os.environ['AI_OPENAI_DEFAULT_MODEL']

    class PromptSettings:
        PROMPT_DIR = find_project_root() / 'ichrisbirch' / 'ai' / 'prompts'

        def __init__(self) -> None:
            self.article_summary_tags = (self.PROMPT_DIR / 'article_summary_tags.txt').read_text()
            self.article_insights = (self.PROMPT_DIR / 'article_insights.txt').read_text()

    def __init__(self) -> None:
        self.openai = self.OpenAISettings()
        self.prompts = self.PromptSettings()


class AuthSettings:
    def __init__(self) -> None:
        self.jwt_secret_key: str = os.environ['AUTH_JWT_SECRET_KEY']
        self.jwt_signing_algorithm: str = os.environ['AUTH_JWT_SIGNING_ALGORITHM']
        self.refresh_token_expire = timedelta(days=30)
        self.access_token_expire = timedelta(minutes=30)
        self.accepting_new_signups: bool = bool(os.environ['AUTH_ACCEPTING_NEW_SIGNUPS'])
        self.no_new_signups_message = 'New signups for VIP users only.'
        self.internal_service_key: str = os.environ['AUTH_INTERNAL_SERVICE_KEY']


class AWSSettings:
    def __init__(self) -> None:
        self.region: str = os.environ['AWS_REGION']
        self.account_id: str = os.environ['AWS_ACCOUNT_ID']
        self.kms_key: str = os.environ['AWS_KMS_KEY']
        self.postgres_backup_role: str = os.environ['AWS_POSTGRES_BACKUP_ROLE'] or 'role/S3DatabaseBackups'
        self.s3_backup_bucket: str = os.environ['AWS_S3_BACKUP_BUCKET']


class ChatSettings:
    def __init__(self) -> None:
        self.host: str = os.environ['CHAT_HOST']
        self.port: int = int(os.environ['CHAT_PORT'])


class FastAPISettings:
    def __init__(self) -> None:
        self.host: str = os.environ['FASTAPI_HOST']
        self.port: int = int(os.environ['FASTAPI_PORT'])
        self.title: str = 'iChrisBirch API'
        self.description: str = """## Backend API for iChrisBirch.com"""
        _protocol = os.environ['PROTOCOL']
        self.allowed_origins: list[str] = [
            '127.0.0.1',
            '127.0.0.1:8505',
            'https://ichrisbirch.com',
            'https://www.ichrisbirch.com',
            'https://chat.ichrisbirch.com',
            f'{_protocol}://localhost',
            f'{_protocol}://localhost:4200',
            f'{_protocol}://localhost:5500',
            f'{_protocol}://localhost:6200',
            f'{_protocol}://localhost:8000',
            f'{_protocol}://localhost:8505',
        ]


class FlaskSettings:
    def __init__(self) -> None:
        self.host: str = os.environ['FLASK_HOST']
        self.port: int = int(os.environ['FLASK_PORT'])
        self.SECRET_KEY: str = os.environ['FLASK_SECRET_KEY']  # MUST be capitalized
        self.TESTING: bool = bool(os.environ['FLASK_TESTING'])
        self.DEBUG: bool = bool(os.environ['FLASK_DEBUG'])
        # For flask-login, use the session to store the `next` value instead of passing as url parameters
        self.USE_SESSION_FOR_NEXT: bool = True
        self.app_id: str = os.environ['FLASK_APP_ID']
        # CSRF token expires after 1 hour (balances security with usability for long sessions)
        self.WTF_CSRF_TIME_LIMIT: int = 3600
        # Session cookie security settings (Traefik handles TLS termination)
        self.SESSION_COOKIE_SECURE: bool = True
        self.SESSION_COOKIE_HTTPONLY: bool = True
        self.SESSION_COOKIE_SAMESITE: str = 'Lax'


class FlaskLoginSettings:
    def __init__(self) -> None:
        self.login_view: str = 'auth.login'
        self.login_message: str = 'Please log in to access this page.'
        self.login_message_category: str = 'info'
        self.REMEMBER_COOKIE_DURATION: timedelta = timedelta(days=1)
        self.REMEMBER_COOKIE_DOMAIN: str = 'ichrisbirch.com'
        self.SESSION_PROTECTION: str = 'strong'


class GithubSettings:
    def __init__(self) -> None:
        self.api_token: str = os.environ['GITHUB_API_TOKEN']
        self.api_url_issues: str = 'https://api.github.com/repos/datapointchris/ichrisbirch/issues'
        self.api_url_labels: str = 'https://api.github.com/repos/datapointchris/ichrisbirch/labels'
        self.api_headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {self.api_token}',
            'X-GitHub-Api-Version': '2022-11-28',
        }


class PlaywrightSettings:
    def __init__(self) -> None:
        self.timeout = 5_000


class PostgresSettings:
    def __init__(self) -> None:
        self.host: str = os.environ['POSTGRES_HOST']
        self.username: str = os.environ['POSTGRES_USERNAME']
        self.password: str = os.environ['POSTGRES_PASSWORD']
        self.port: int = int(os.environ['POSTGRES_PORT'])
        self.database: str = os.environ['POSTGRES_DB']
        self.db_schemas: list[str] = [schema.strip() for schema in os.environ['POSTGRES_DB_SCHEMAS'].split(',')]

    @property
    def db_uri(self) -> str:
        return f'postgresql+psycopg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}'


class RedisSettings:
    def __init__(self) -> None:
        self.host: str = os.environ['REDIS_HOST']
        self.password: str = os.environ['REDIS_PASSWORD']
        self.port: int = int(os.environ['REDIS_PORT'])
        self.db: int = int(os.environ['REDIS_DB'])


class SQLAlchemySettings:
    def __init__(self) -> None:
        self.echo: bool = False
        self.track_modifications: bool = False
        self.host: str = os.environ['POSTGRES_HOST']
        self.username: str = os.environ['POSTGRES_USERNAME']
        self.password: str = os.environ['POSTGRES_PASSWORD']
        self.port: int = int(os.environ['POSTGRES_PORT'])
        self.database: str = os.environ['POSTGRES_DB']

    @property
    def db_uri(self) -> str:
        return f'postgresql+psycopg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}'


class UsersSettings:
    def __init__(self) -> None:
        self.default_regular_user_name = os.environ['USERS_DEFAULT_REGULAR_USER_NAME']
        self.default_regular_user_email = os.environ['USERS_DEFAULT_REGULAR_USER_EMAIL']
        self.default_regular_user_password = os.environ['USERS_DEFAULT_REGULAR_USER_PASSWORD']

        self.default_admin_user_name = os.environ['USERS_DEFAULT_ADMIN_USER_NAME']
        self.default_admin_user_email = os.environ['USERS_DEFAULT_ADMIN_USER_EMAIL']
        self.default_admin_user_password = os.environ['USERS_DEFAULT_ADMIN_USER_PASSWORD']

        # Service account settings removed - now using API key authentication


class Settings:
    def __init__(self):
        self.name: str = 'ichrisbirch'
        self.ENVIRONMENT: str = os.environ['ENVIRONMENT']
        self.global_timezone = 'US/Eastern'
        self.protocol = os.environ['PROTOCOL']
        self.mac_safari_request_headers = {
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.4 Safari/605.1.15'
            ),
        }

        self.ai = AISettings()
        self.auth = AuthSettings()
        self.aws = AWSSettings()
        self.chat = ChatSettings()
        self.fastapi = FastAPISettings()
        self.flask = FlaskSettings()
        self.flasklogin = FlaskLoginSettings()
        self.github = GithubSettings()
        self.playwright = PlaywrightSettings()
        self.postgres = PostgresSettings()
        self.redis = RedisSettings()
        self.sqlalchemy = SQLAlchemySettings()
        self.users = UsersSettings()

    @property
    def api_url(self) -> str:
        port = f':{self.fastapi.port}' if self.fastapi.port else ''
        return f'{self.protocol}://{self.fastapi.host}{port}'

    @property
    def chat_url(self) -> str:
        port = f':{self.chat.port}' if self.chat.port else ''
        return f'{self.protocol}://{self.chat.host}{port}'


def _set_environment_variables(env: str):
    ssm = boto3.client('ssm', region_name='us-east-2')
    all_params = []
    response = ssm.get_parameters_by_path(Path=f'/ichrisbirch/{env}/', Recursive=True, WithDecryption=True)
    all_params.extend(response['Parameters'])
    while 'NextToken' in response:
        response = ssm.get_parameters_by_path(
            Path=f'/ichrisbirch/{env}/', Recursive=True, WithDecryption=True, NextToken=response['NextToken']
        )
        all_params.extend(response['Parameters'])
    for param in all_params:
        trimmed = param['Name'].replace(f'/ichrisbirch/{env}/', '')
        env_var_name = '_'.join(trimmed.split('/')).upper()
        os.environ[env_var_name] = param['Value']


@log_caller
@functools.cache
def get_settings():
    env_before = os.environ['ENVIRONMENT']
    if dotenv.load_dotenv():
        env_after = os.environ['ENVIRONMENT']
        logger.info(f'{env_after} environment variables loaded from .env file')
        if env_before != env_after:
            logger.warning(f'ENVIRONMENT changed from {env_before} to {env_after} after loading .env file')
    else:
        logger.info('no .env file found, loading from SSM parameters')
        _set_environment_variables(env_before)
        logger.info('environment variables set from SSM parameters')
    return Settings()


settings = get_settings()
