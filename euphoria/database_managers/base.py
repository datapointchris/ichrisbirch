from abc import ABC, abstractmethod


class PostgresManager(ABC):
    @abstractmethod
    def init_app(self, app):
        pass

    @abstractmethod
    def create_all(self, app):
        pass


class SQLiteManager(ABC):
    @abstractmethod
    def init_app(self, app):
        pass

    @abstractmethod
    def create_all(self, app):
        pass


class MongoManager(ABC):
    @abstractmethod
    def init_app(self, app):
        pass

    @abstractmethod
    def create_all(self, app):
        pass
