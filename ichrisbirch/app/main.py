import logging

from flask import Flask

from ichrisbirch.app.routes import (
    autotasks,
    box_packing,
    countdowns,
    events,
    habits,
    health,
    home,
    journal,
    portfolio,
    tasks,
)
from ichrisbirch.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Flask app factory

    Returns:
        Flask: Flask app
    """
    app = Flask(__name__)
    logger.debug(f'{app.import_name} App Started')

    with app.app_context():
        app.config.from_object(settings.flask)
        logger.debug('Configured Flask App')
        logger.debug(f'Flask App Config: {app.config.keys()}')

        app.register_blueprint(home.blueprint)
        app.register_blueprint(autotasks.blueprint, url_prefix='/autotasks')
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
