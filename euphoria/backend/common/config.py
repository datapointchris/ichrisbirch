import os
import dotenv

dotenv.load_dotenv()


class EnvironmentConfig:
    CSRF_ENABLED: bool = True
    SECRET_KEY: str = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    TESTING: bool
    DEVELOPMENT: bool
    SQLALCHEMY_ECHO: bool
    API_URL: str
    SCHEMAS: list[str] = ['apartments', 'box_packing', 'habits']

    POSTGRES_URI: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    MONGODB_URI: str
    MONGODB_USER: str
    MONGODB_PASSWORD: str

    DYNAMODB_URL: str
    DYNAMODB_USER: str
    DYNAMODB_PASSWORD: str

    POSTGRES_DATABASE_URI: str
    MONGODB_DATABASE_URI: str
    DYNAMODB_DATABASE_URI: str
    SQLITE_DATABASE_URI: str
    SQLALCHEMY_DATABASE_URI: str


class DevelopmentConfig(EnvironmentConfig):
    TESTING = False
    DEVELOPMENT = True
    SQLALCHEMY_ECHO = True
    API_URL = os.environ.get('DEV_API_URL')

    POSTGRES_URI = os.environ.get('DEV_POSTGRES_URI')
    POSTGRES_USER = os.environ.get('DEV_POSTGRES_USER')
    POSTGRES_PASSWORD = os.environ.get('DEV_POSTGRES_PASSWORD')

    MONGODB_URI = os.environ.get('DEV_MONGODB_URI')
    MONGODB_USER = os.environ.get('DEV_MONGODB_USER')
    MONGODB_PASSWORD = os.environ.get('DEV_MONGODB_PASSWORD')

    DYNAMODB_URL = os.environ.get('PROD_DYNAMODB_URL')
    DYNAMODB_USER = os.environ.get('PROD_DYNAMODB_USER')
    DYNAMODB_PASSWORD = os.environ.get('PROD_DYNAMODB_PASSWORD')

    POSTGRES_DATABASE_URI = f'{POSTGRES_URI}/euphoria'
    MONGODB_DATABASE_URI = f'{MONGODB_URI}/euphoria'
    DYNAMODB_DATABASE_URI = os.environ.get('DEV_DYNAMODB_DATABASE_URI')
    SQLITE_DATABASE_URI = os.environ.get('DEV_SQLITE_DATABASE_URI')
    SQLALCHEMY_DATABASE_URI = POSTGRES_DATABASE_URI


class TestingConfig(EnvironmentConfig):
    TESTING = True
    DEVELOPMENT = True
    SQLALCHEMY_ECHO = True
    API_URL = os.environ.get('TEST_API_URL')

    POSTGRES_URI = os.environ.get('TEST_POSTGRES_URI')
    POSTGRES_USER = os.environ.get('TEST_POSTGRES_USER')
    POSTGRES_PASSWORD = os.environ.get('TEST_POSTGRES_PASSWORD')

    MONGODB_URI = os.environ.get('PROD_MONGODB_URI')
    MONGODB_USER = os.environ.get('PROD_MONGODB_USER')
    MONGODB_PASSWORD = os.environ.get('PROD_MONGODB_PASSWORD')

    DYNAMODB_URL = os.environ.get('PROD_DYNAMODB_URL')
    DYNAMODB_USER = os.environ.get('PROD_DYNAMODB_USER')
    DYNAMODB_PASSWORD = os.environ.get('PROD_DYNAMODB_PASSWORD')

    POSTGRES_DATABASE_URI = (
        f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_URI}:5432/euphoria'
    )
    MONGODB_DATABASE_URI = f'mongodb+srv://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_URI}/euphoria?retryWrites=true&w=majority'
    DYNAMODB_DATABASE_URI = os.environ.get('TEST_DYNAMODB_DATABASE_URI')
    SQLITE_DATABASE_URI = os.environ.get('TEST_SQLITE_DATABASE_URI')
    SQLALCHEMY_DATABASE_URI = POSTGRES_DATABASE_URI


class ProductionConfig(EnvironmentConfig):
    TESTING = False
    DEVELOPMENT = False
    SQLALCHEMY_ECHO = True
    API_URL = os.environ.get('PROD_API_URL')

    POSTGRES_URI = os.environ.get('PROD_POSTGRES_URI')
    POSTGRES_USER = os.environ.get('PROD_POSTGRES_USER')
    POSTGRES_PASSWORD = os.environ.get('PROD_POSTGRES_PASSWORD')

    MONGODB_URI = os.environ.get('PROD_MONGODB_URI')
    MONGODB_USER = os.environ.get('PROD_MONGODB_USER')
    MONGODB_PASSWORD = os.environ.get('PROD_MONGODB_PASSWORD')

    DYNAMODB_URL = os.environ.get('PROD_DYNAMODB_URL')
    DYNAMODB_USER = os.environ.get('PROD_DYNAMODB_USER')
    DYNAMODB_PASSWORD = os.environ.get('PROD_DYNAMODB_PASSWORD')

    POSTGRES_DATABASE_URI = (
        f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_URI}:5432/euphoria'
    )
    MONGODB_DATABASE_URI = f'mongodb+srv://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_URI}/euphoria?retryWrites=true&w=majority'
    DYNAMODB_DATABASE_URI = os.environ.get('PROD_DYNAMODB_DATABASE_URI')
    SQLITE_DATABASE_URI = os.environ.get('PROD_SQLITE_DATABASE_URI')
    SQLALCHEMY_DATABASE_URI = POSTGRES_DATABASE_URI


def get_config_for_environment(environment: str = None) -> EnvironmentConfig:
    """Configures app for specified environment

    Args:
        environment:
            `development`
            `testing`
            `production`

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
