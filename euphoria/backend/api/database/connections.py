import psycopg


class PostgresConnection:
    """Wrapper for psycopg connection"""
    def __init__(self, connection_string, *args, **kwargs):
        self.connection_string = connection_string
        self.args = args
        self.kwargs = kwargs

    def connect(self) -> psycopg.Connection:
        return psycopg.connect(
            self.connection_string, *self.args, **self.kwargs, autocommit=True
        )


class MongoDBConnection:
    def __init__(self, user, name, password):
        self.user = user
        self.name = name
        self.password = password


class DynamoDBConnection:
    def __init__(self, user, name, password):
        self.user = user
        self.name = name
        self.password = password


class SQLiteConnection:
    def __init__(self, user, name, password):
        self.user = user
        self.name = name
        self.password = password
