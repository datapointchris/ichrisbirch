import os
import dotenv
import logging
from pydantic import BaseSettings


match environment := os.getenv('ENVIRONMENT'):
    case 'development':
        dotenv.find_dotenv('.dev.env')
    case 'testing':
        dotenv.find_dotenv('.test.env')
    case 'production':
        dotenv.find_dotenv('.prod.env')
    case _:
        raise ValueError(
            f'Unrecognized Environment Variable: {environment}'
            'Did you set ENVIRONMENT before starting the program?'
        )


class PostgresSettings(BaseSettings):
    POSTGRES_URI: str = os.getenv('POSTGRES_URI')
    POSTGRES_USER: str = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_DATABASE_URI: str = (
        f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_URI}:5432/euphoria'
    )


class SQLAlchemySettings(BaseSettings):
    SQLALCHEMY_ECHO: bool = True
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SECRET_KEY: str = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI: str = PostgresSettings.POSTGRES_DATABASE_URI


class MongoDBSettings(BaseSettings):
    MONGODB_URI: str = os.getenv('MONGODB_URI')
    MONGODB_USER: str = os.getenv('MONGODB_USER')
    MONGODB_PASSWORD: str = os.getenv('MONGODB_PASSWORD')
    MONGODB_DATABASE_URI: str = f'mongodb+srv://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_URI}/euphoria?retryWrites=true&w=majority'


class DynamoDBSettings(BaseSettings):
    DYNAMODB_URL: str = os.getenv('DYNAMODB_URL')
    DYNAMODB_USER: str = os.getenv('DYNAMODB_USER')
    DYNAMODB_PASSWORD: str = os.getenv('DYNAMODB_PASSWORD')
    DYNAMODB_DATABASE_URI: str = os.getenv('DYNAMODB_DATABASE_URI')


class SQLiteSettings(BaseSettings):
    SQLITE_DATABASE_URI: str = os.getenv('SQLITE_DATABASE_URI')


class LoggingSettings(BaseSettings):
    LOGGING_LEVEL: int = logging.INFO


class Settings(BaseSettings):
    ENVIRONMENT: str = os.getenv('ENVIRONMENT')
    CSRF_ENABLED: bool = True
    API_URL: str = os.getenv('API_URL')
    DB_SCHEMAS: list[str] = ['apartments', 'box_packing', 'habits']

    postgres: PostgresSettings = PostgresSettings()
    sqlalchemy: SQLAlchemySettings = SQLAlchemySettings()
    mongodb: MongoDBSettings = MongoDBSettings()
    dynamodb: DynamoDBSettings = DynamoDBSettings()
    sqlite: SQLiteSettings = SQLiteSettings()
    logging: LoggingSettings = LoggingSettings()


SETTINGS = Settings()
