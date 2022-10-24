import os
import dotenv
import logging
from dataclasses import dataclass, field


environment = os.getenv('ENVIRONMENT')
print('ENVIRO: ', environment)
match environment:
    case 'development':
        dotenv.load_dotenv(dotenv.find_dotenv('.dev.env'))
    case 'testing':
        dotenv.load_dotenv(dotenv.find_dotenv('.test.env'))
    case 'production':
        dotenv.load_dotenv(dotenv.find_dotenv('.prod.env'))
        print("LOADED PROD")
        print(os.getenv('API_URL'))
        print("dotenv is here:", dotenv.find_dotenv('.prod.env'))
    case _:
        raise ValueError(
            f'Unrecognized Environment Variable: {environment}\n'
            'Did you set ENVIRONMENT before starting the program?'
        )


@dataclass
class FlaskSettings:
    SECRET_KEY: str = os.getenv('SECRET_KEY')


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
    LOGGING_LEVEL: int = logging.INFO


@dataclass
class Settings:
    ENVIRONMENT: str = os.getenv('ENVIRONMENT')
    API_URL: str = os.getenv('API_URL')
    DB_SCHEMAS: list[str] = field(default_factory=lambda: ['apartments', 'box_packing', 'habits'])

    flask: FlaskSettings = FlaskSettings()
    postgres: PostgresSettings = PostgresSettings()
    sqlalchemy: SQLAlchemySettings = SQLAlchemySettings()
    mongodb: MongoDBSettings = MongoDBSettings()
    dynamodb: DynamoDBSettings = DynamoDBSettings()
    sqlite: SQLiteSettings = SQLiteSettings()
    logging: LoggingSettings = LoggingSettings()

    sqlalchemy.SQLALCHEMY_DATABASE_URI = postgres.POSTGRES_DATABASE_URI


SETTINGS = Settings()
