import os

import config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.schema import CreateSchema
from flask_marshmallow import Marshmallow

from euphoria.database import DynamoDBConnection, MongoDBConnection
from euphoria.api import register_api

db = SQLAlchemy()
mongodb = MongoDBConnection()
dynamodb = DynamoDBConnection()

ma = Marshmallow()

def create_app():
    app = Flask(__name__)
    env = os.environ.get('FLASK_ENV')
    env_object = config.get_env_config(env)
    app.config.from_object(env_object)

    db.init_app(app)
    mongodb.init_app(app)
    dynamodb.init_app(app)

    ma.init_app(app)

    # Blueprints
    from euphoria.apartments.routes import apartments_bp
    from euphoria.home.routes import home_bp
    from euphoria.moving.routes import moving_bp
    from euphoria.portfolio.routes import portfolio_bp
    from euphoria.tasks.routes import tasks_bp
    from euphoria.tracks.routes import tracks_bp

    # APIs
    from euphoria.api.tasks import TaskAPI

    with app.app_context():
        app.register_blueprint(home_bp)
        app.register_blueprint(portfolio_bp, url_prefix='/portfolio')
        app.register_blueprint(apartments_bp, url_prefix='/apartments')
        app.register_blueprint(moving_bp, url_prefix='/moving')
        app.register_blueprint(tracks_bp, url_prefix='/tracks')
        app.register_blueprint(tasks_bp, url_prefix='/tasks')

        register_api(app, TaskAPI, TaskAPI.VERSION, 'tasks_api', '/tasks')

        # Have yet to figure out a better way to do this
        schemas = ['tracks', 'tasks', 'moving', 'apartments', 'porfolio']
        for schema in schemas:
            if not db.engine.dialect.has_schema(db.engine, schema):
                db.session.execute(CreateSchema(schema))
                db.session.commit()
        db.create_all()

    return app
