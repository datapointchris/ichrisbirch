import logging

from flask import Flask, render_template

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
from ichrisbirch.config import Settings

logger = logging.getLogger(__name__)


def handle_404_error(e):
    a_msg = e.description.get('abort_message')
    e_msg = e.description.get('error_message')
    template = render_template('404.html', abort_message=a_msg, error_message=e_msg)
    return (template, 404)


def handle_500_error(e):
    a_msg = e.description.get('abort_message')
    e_msg = e.description.get('error_message')
    template = render_template('500.html', abort_message=a_msg, error_message=e_msg)
    return (template, 500)


def create_app(settings: Settings) -> Flask:
    app = Flask(__name__)
    logger.info('Flask App Created')

    with app.app_context():
        app.config.from_object(settings.flask)
        logger.info('Flask App Configured')
        logger.debug(
            f'DEBUG={app.config.get("DEBUG")}, TESTING={app.config.get("TESTING")}, ENV={app.config.get("ENV")}'
        )

        app.register_error_handler(404, handle_404_error)
        app.register_error_handler(500, handle_500_error)
        logger.info('Flask App Error Handlers Registered')

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
        logger.info('Flask App Blueprints Registered')
    return app
