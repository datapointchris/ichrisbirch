import functools
import os
import sys
from datetime import timedelta
from pathlib import Path

import dotenv
import structlog

from ichrisbirch.util import find_project_root

logger = structlog.get_logger()


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
        self.domain: str = os.environ.get('DOMAIN', 'ichrisbirch.com')
        self.app_id: str = os.environ.get('APP_ID', '')
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
        self.github = GithubSettings()
        self.playwright = PlaywrightSettings()
        self.postgres = PostgresSettings()
        self.redis = RedisSettings()
        self.sqlalchemy = SQLAlchemySettings()
        self.users = UsersSettings()

    @property
    def api_url(self) -> str:
        """Internal API URL for service-to-service communication."""
        port = f':{self.fastapi.port}' if self.fastapi.port else ''
        return f'{self.protocol}://{self.fastapi.host}{port}'

    @property
    def chat_url(self) -> str:
        """Internal chat URL for service-to-service communication."""
        port = f':{self.chat.port}' if self.chat.port else ''
        return f'{self.protocol}://{self.chat.host}{port}'

    @property
    def api_url_external(self) -> str:
        """External API URL for user-facing links."""
        return f'https://api.{self.domain}'

    @property
    def chat_url_external(self) -> str:
        """External chat URL for user-facing links."""
        return f'https://chat.{self.domain}'


def _detect_environment() -> str:
    """Detect environment with sensible defaults for development.

    Priority:
    1. Explicit ENVIRONMENT env var (highest priority)
    2. Auto-detect pytest (before .env to ensure tests use 'testing')
    3. ENVIRONMENT from .env file if it exists
    4. Default to 'development'
    """
    if env := os.environ.get('ENVIRONMENT'):
        return env

    if 'pytest' in sys.modules:
        return 'testing'

    if Path('.env').exists():
        dotenv.load_dotenv()
        if env := os.environ.get('ENVIRONMENT'):
            return env

    return 'development'


# @log_caller
@functools.cache
def get_settings():
    env = _detect_environment()
    os.environ['ENVIRONMENT'] = env

    if dotenv.load_dotenv():
        logger.info('config_loaded_from_dotenv', environment=env)
    elif os.environ.get('POSTGRES_HOST'):
        logger.info('config_loaded_from_environment', environment=env)
    else:
        raise FileNotFoundError(
            f'.env file not found for environment={env}. For production, decrypt secrets: sops decrypt secrets/secrets.prod.enc.env > .env'
        )

    return Settings()
