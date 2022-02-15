from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymongo
from euphoria.apartments.db_manager import ApartmentsDBManager
from euphoria.moving.db_manager import BoxDBManager
from euphoria.tracks.mongomanagers import (
    HabitsDBManager,
    JournalDBManager,
    CountdownsDBManager,
)


# from database import database

# DATABASES #
# TODO: These need to have the same DB format, probably a base class or protocol!!!!
# Make them take the same connection maybe even.  Just grab the tables for each connection

event_db = SQLAlchemy()
apt_db = ApartmentsDBManager('apartments.db')
box_db = BoxDBManager('moving.db')

MONGODB_LOCAL = 'mongodb://127.0.0.1:27017'
DATABASE = 'tracks'
CLIENT = pymongo.MongoClient(MONGODB_LOCAL)
habit_db = HabitsDBManager(client=CLIENT, database=DATABASE, collection='habits')
journal_db = JournalDBManager(client=CLIENT, database=DATABASE, collection='journal')
countdown_db = CountdownsDBManager(
    client=CLIENT, database=DATABASE, collection='countdowns'
)

# Blueprints
from euphoria.home.routes import home_bp
from euphoria.cockpit.routes import cockpit_bp
from euphoria.portfolio.routes import portfolio_bp
from euphoria.apartments.routes import apartments_bp
from euphoria.moving.routes import moving_bp
from euphoria.tracks.routes import tracks_bp


def create_app():
    app = Flask(__name__)
    # setup with the configuration provided
    # app.config.from_object('config.DevelopmentConfig')

    # hardcoded for now for testing
    # TODO: this database URI will eventually be the postgres installation
    # TODO: it also should end up in the config file so it gets configured automatically and
    # does not leave the config out in the open
    # TODO: use instance folder here --> Must research first
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'

    app.config['MONGODB_DATABASE_URI'] = 'mongodb://127.0.0.1:27017'

    # TODO: This is something I need to research more
    # Initialize plugins

    # TODO: Eventually these won't be separate managers that need init
    # They will be the same db but point to different tables
    # TODO: How do I do advanced functionality in SQL with SQLAlchemy?
    # apt_db.init_app(app)
    # box_db.init_app(app)
    # habit_db.init_app(app)
    # box_db.init_app(app)
    # countdown_db.init_app(app)

    event_db.init_app(app)

    with app.app_context():
        app.register_blueprint(home_bp)
        app.register_blueprint(cockpit_bp, url_prefix='/cockpit')
        app.register_blueprint(portfolio_bp, url_prefix='/portfolio')
        app.register_blueprint(apartments_bp, url_prefix='/apartments')
        app.register_blueprint(moving_bp, url_prefix='/moving')
        app.register_blueprint(tracks_bp, url_prefix='/tracks')

        event_db.create_all()

        return app
