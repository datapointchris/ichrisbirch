from flask import Flask
from .routes import main, box_packing, countdowns, events, journal, habits, portfolio, tasks
from ..common.config import env_config


def create_app():
    app = Flask(__name__)

    with app.app_context():
        app.config.from_object(env_config)

        app.register_blueprint(main.blueprint)
        app.register_blueprint(portfolio.blueprint, url_prefix='/portfolio')
        app.register_blueprint(box_packing.blueprint, url_prefix='/box-packing')
        app.register_blueprint(countdowns.blueprint, url_prefix='/countdowns')
        app.register_blueprint(events.blueprint, url_prefix='/events')
        app.register_blueprint(journal.blueprint, url_prefix='/journal')
        app.register_blueprint(habits.blueprint, url_prefix='/habits')
        app.register_blueprint(tasks.blueprint, url_prefix='/tasks')

    return app
