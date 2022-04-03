from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from euphoria.database_managers.apartments import ApartmentsDBManager
from euphoria.database_managers.moving import BoxDBManager

from euphoria.database_managers.tracks import (
    HabitsDBManager,
    JournalDBManager,
    CountdownsDBManager,
)


import dotenv

# this should load the FLASK_ENV variable and set the environment
dotenv.load_dotenv()

# Postgres
priorities_db = SQLAlchemy()
events_db = SQLAlchemy()
apt_db = ApartmentsDBManager()
box_db = BoxDBManager()

# MongoDB
habits_db = HabitsDBManager()
journal_db = JournalDBManager()
countdowns_db = CountdownsDBManager()

# Blueprints (cannot import at top due to circular imports)
from euphoria.home.routes import home_bp
from euphoria.cockpit.routes import cockpit_bp
from euphoria.portfolio.routes import portfolio_bp
from euphoria.apartments.routes import apartments_bp
from euphoria.moving.routes import moving_bp
from euphoria.tracks.routes import tracks_bp
from euphoria.priorities.routes import priorities_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.DevelopmentConfig')

    apt_db.init_app(app)
    box_db.init_app(app)
    events_db.init_app(app)
    priorities_db.init_app(app)
    habits_db.init_app(app, db='tracks', collection='habits')
    journal_db.init_app(app, db='tracks', collection='journal')
    countdowns_db.init_app(app, db='tracks', collection='countdowns')

    with app.app_context():
        app.register_blueprint(home_bp)
        app.register_blueprint(cockpit_bp, url_prefix='/cockpit')
        app.register_blueprint(portfolio_bp, url_prefix='/portfolio')
        app.register_blueprint(apartments_bp, url_prefix='/apartments')
        app.register_blueprint(moving_bp, url_prefix='/moving')
        app.register_blueprint(tracks_bp, url_prefix='/tracks')
        app.register_blueprint(priorities_bp, url_prefix='/priorities')

        priorities_db.create_all()
        events_db.create_all()
        apt_db.create_all()
        box_db.create_all()

    return app
