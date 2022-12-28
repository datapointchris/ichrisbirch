import os
import dotenv
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

NAME: str = 'ichrisbirch.com'
DB_SCHEMAS: list[str] = ['apartments', 'box_packing', 'habits']
ENVIRONMENT: str = os.getenv('ENVIRONMENT')

match ENVIRONMENT:
    case 'development':
        env_file = dotenv.find_dotenv('.dev.env')
        dotenv.load_dotenv(env_file)
    case 'testing':
        env_file = dotenv.find_dotenv('.test.env')
        dotenv.load_dotenv(env_file)
    case 'production':
        env_file = dotenv.find_dotenv('.prod.env')
        dotenv.load_dotenv(env_file)
    case _:
        raise ValueError(
            f'Unrecognized Environment Variable: {ENVIRONMENT}\n'
            'Did you set ENVIRONMENT before starting the program?'
        )

API_URL: str = os.getenv('API_URL')
LOG_LEVEL: str = os.getenv('LOG_LEVEL')

logger.debug(f"Starting: {NAME}")
logger.debug(f"Loaded: {env_file}")
logger.debug(f"Environment: {ENVIRONMENT}")
logger.debug(f"API URL: {API_URL}")
logger.debug(f"Log level: {LOG_LEVEL}")


@dataclass
class FlaskSettings:
    SECRET_KEY: str = os.getenv('SECRET_KEY')
    ENV: str = ENVIRONMENT


@dataclass
class PostgresSettings:
    POSTGRES_URI: str = os.getenv('POSTGRES_URI')
    POSTGRES_USER: str = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_DATABASE_URI: str = (
        f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_URI}:5432/euphoria'
    )


@dataclass
class SQLAlchemySettings:
    SQLALCHEMY_ECHO: bool = True
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_DATABASE_URI: str = ""


@dataclass
class MongoDBSettings:
    MONGODB_URI: str = os.getenv('MONGODB_URI')
    MONGODB_USER: str = os.getenv('MONGODB_USER')
    MONGODB_PASSWORD: str = os.getenv('MONGODB_PASSWORD')
    MONGODB_DATABASE_URI: str = f'mongodb+srv://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_URI}/euphoria?retryWrites=true&w=majority'


@dataclass
class DynamoDBSettings:
    DYNAMODB_URL: str = os.getenv('DYNAMODB_URL')
    DYNAMODB_USER: str = os.getenv('DYNAMODB_USER')
    DYNAMODB_PASSWORD: str = os.getenv('DYNAMODB_PASSWORD')
    DYNAMODB_DATABASE_URI: str = os.getenv('DYNAMODB_DATABASE_URI')


@dataclass
class SQLiteSettings:
    SQLITE_DATABASE_URI: str = os.getenv('SQLITE_DATABASE_URI')


@dataclass
class LoggingSettings:
    LOG_LEVEL: int = logging.getLevelName(LOG_LEVEL)


log = LoggingSettings()
flask = FlaskSettings()
sqlite = SQLiteSettings()
mongodb = MongoDBSettings()
dynamodb = DynamoDBSettings()
postgres = PostgresSettings()
sqlalchemy = SQLAlchemySettings()
sqlalchemy.SQLALCHEMY_DATABASE_URI = postgres.POSTGRES_DATABASE_URI
