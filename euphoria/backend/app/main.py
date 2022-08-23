from flask import Flask
import sqlalchemy
from .routes import main, box_packing, countdowns, events, journal, habits, portfolio, tasks
from ..common.config import get_config_for_environment


# TODO: Delete this when moving to Alembic migrations
# It is only here to create tables on the first run
# from .models.tasks import Task
# from .db.base_class import Base, engine

# Base.metadata.create_all(bind=engine)


def create_app():
    app = Flask(__name__)
    config_object = get_config_for_environment()

    with app.app_context():
        app.config.from_object(config_object)

        app.register_blueprint(main.blueprint)
        app.register_blueprint(portfolio.blueprint, url_prefix='/portfolio')
        app.register_blueprint(box_packing.blueprint, url_prefix='/box-packing')
        app.register_blueprint(countdowns.blueprint, url_prefix='/countdowns')
        app.register_blueprint(events.blueprint, url_prefix='/events')
        app.register_blueprint(journal.blueprint, url_prefix='/journal')
        app.register_blueprint(habits.blueprint, url_prefix='/habits')
        app.register_blueprint(tasks.blueprint, url_prefix='/tasks')

    return app
