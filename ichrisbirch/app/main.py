import logging

from flask import Flask

from ichrisbirch import settings
from ichrisbirch.app.routes import box_packing, countdowns, events, habits, health, journal, main, portfolio, tasks

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Flask app factory

    Returns:
        app: Flask app
    """
    app = Flask(__name__)
    logger.debug(f'{app.import_name} App Started')

    with app.app_context():
        app.config.from_object(settings.flask)
        logger.debug('Configured App')

        app.register_blueprint(main.blueprint)
        app.register_blueprint(box_packing.blueprint, url_prefix='/box-packing')
        app.register_blueprint(countdowns.blueprint, url_prefix='/countdowns')
        app.register_blueprint(events.blueprint, url_prefix='/events')
        app.register_blueprint(habits.blueprint, url_prefix='/habits')
        app.register_blueprint(health.blueprint, url_prefix='/health')
        app.register_blueprint(journal.blueprint, url_prefix='/journal')
        app.register_blueprint(portfolio.blueprint, url_prefix='/portfolio')
        app.register_blueprint(tasks.blueprint, url_prefix='/tasks')
        logger.debug('Registered App Blueprints')
    return app
