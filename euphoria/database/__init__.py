from flask import Flask
from pymongo import MongoClient
import pymongo
from pymongo import uri_parser


class MongoDBConnection:
    """Wrapper class for MongoClient to mimic SQLAlchemy behavior

    Example:
    >>> app = Flask()
    >>> mongodb = MongoConnection()
    >>> mongodb.init_app(app)
    >>> mongodb.execute()

    """

    def __init__(self, db=None):
        self.db = db

    def init_app(self, app: Flask) -> MongoClient:
        host = app.config.get('MONGODB_DATABASE_URI')
        client = pymongo.MongoClient(host)
        db_name = uri_parser.parse_uri(host)['database']
        self.db = client[db_name]



class DynamoDBConnection:
    """Wrapper class for DynamoDB connection to mimic SQLAlchemy behavior"""

    def init_app(self, app: Flask) -> str:
        return 'Not Implemented'
