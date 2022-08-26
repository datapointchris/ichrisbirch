import os
import dotenv
from enum import Enum, auto

dotenv.load_dotenv()


class EnvironmentConfig:
    CSRF_ENABLED = True
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEVELOPMENT: str
    TESTING: str

    DYNAMODB_DATABASE_URI: str
    SQLITE_DATABASE_URI: str

    MONGODB_URL: str
    MONGODB_USER: str
    MONGODB_PASSWORD: str
    MONGODB_DATABASE_URI: str

    POSTGRES_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DATABASE_URI: str


class DevelopmentConfig(EnvironmentConfig):
    TESTING = False
    DEVELOPMENT = True
    SQLALCHEMY_ECHO = True
    API_URL = os.environ.get('DEV_API_URL')
    DYNAMODB_DATABASE_URI = os.environ.get('DEV_DYNAMODB_DATABASE_URI')
    SQLITE_DATABASE_URI = os.environ.get('DEV_SQLITE_DATABASE_URI')

    MONGODB_URL = os.environ.get('DEV_MONGODB_URL')
    MONGODB_USER = os.environ.get('DEV_MONGODB_USER')
    MONGODB_PASSWORD = os.environ.get('DEV_MONGODB_PASSWORD')
    MONGODB_DATABASE_URI = f'{MONGODB_URL}/euphoria'

    POSTGRES_URL = os.environ.get('DEV_POSTGRES_URL')
    POSTGRES_USER = os.environ.get('DEV_POSTGRES_USER')
    POSTGRES_PASSWORD = os.environ.get('DEV_POSTGRES_PASSWORD')
    SQLALCHEMY_DATABASE_URI = f'{POSTGRES_URL}/euphoria'


class TestingConfig(EnvironmentConfig):
    TESTING = True
    DEVELOPMENT = True
    SQLALCHEMY_ECHO = True
    API_URL = os.environ.get('TEST_API_URL')
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_SQLALCHEMY_DATABASE_URI')
    DYNAMODB_DATABASE_URI = os.environ.get('TEST_DYNAMODB_DATABASE_URI')
    MONGODB_DATABASE_URI = os.environ.get('TEST_MONGODB_DATABASE_URI')
    SQLITE_DATABASE_URI = os.environ.get('TEST_SQLITE_DATABASE_URI')


class ProductionConfig(EnvironmentConfig):
    TESTING = False
    DEVELOPMENT = False
    SQLALCHEMY_ECHO = True
    API_URL = os.environ.get('PROD_API_URL')
    DYNAMODB_DATABASE_URI = os.environ.get('PROD_DYNAMODB_DATABASE_URI')
    SQLITE_DATABASE_URI = os.environ.get('PROD_SQLITE_DATABASE_URI')

    MONGODB_URL = os.environ.get('PROD_MONGODB_URL')
    MONGODB_USER = os.environ.get('PROD_MONGODB_USER')
    MONGODB_PASSWORD = os.environ.get('PROD_MONGODB_PASSWORD')
    MONGODB_DATABASE_URI = f'mongodb+srv://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_URL}/euphoria?retryWrites=true&w=majority'
    POSTGRES_URL = os.environ.get('PROD_POSTGRES_URL')
    POSTGRES_USER = os.environ.get('PROD_POSTGRES_USER')
    POSTGRES_PASSWORD = os.environ.get('PROD_POSTGRES_PASSWORD')
    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_URL}:5432/euphoria'
    )


def get_config_for_environment(environment: str = 'production') -> EnvironmentConfig:
    """Configures app for specified environment

    Args:
        environment:
            `development`
            `testing`
            `production`
        Default: `production`

    Returns:
        EnvironmentConfig: Configuration object for selected environment
    """
    match environment:
        case 'development':
            return DevelopmentConfig
        case 'testing':
            return TestingConfig
        case 'production':
            return ProductionConfig
        case _:
            raise ValueError(
                f'Unrecognized Environment Variable: {environment}'
                '  --> Did you set ENVIRONMENT before starting the program?'
            )


env_config = get_config_for_environment(os.environ.get('ENVIRONMENT'))
