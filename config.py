import os
import dotenv

dotenv.load_dotenv()


class Config(object):
    CSRF_ENABLED = True
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    TESTING = False
    DEVELOPMENT = True
    SQLALCHEMY_ECHO = True
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

    API_URL = os.environ.get('DEV_API_URL')


class TestingConfig(Config):
    TESTING = True
    DEVELOPMENT = True
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_SQLALCHEMY_DATABASE_URI')
    DYNAMODB_DATABASE_URI = os.environ.get('TEST_DYNAMODB_DATABASE_URI')
    MONGODB_DATABASE_URI = os.environ.get('TEST_MONGODB_DATABASE_URI')
    SQLITE_DATABASE_URI = os.environ.get('TEST_SQLITE_DATABASE_URI')

    API_URL = os.environ.get('TEST_API_URL')


class ProductionConfig(Config):
    TESTING = False
    DEVELOPMENT = False
    SQLALCHEMY_ECHO = True
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

    API_URL = os.environ.get('PROD_API_URL')


def get_env_config(environment: str) -> Config:
    """Configures app for specified environment

    Args:
        environment (str): One of 'development', 'testing', 'production'
        Defaults to 'production'

    Returns:
        Config: Configuration object for selected environment
    """
    envs = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig,
    }
    return envs.get(environment, ProductionConfig)
