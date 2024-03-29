import http
import logging
from functools import partial

from flask import Flask, render_template

from ichrisbirch.app.routes import (
    autotasks,
    box_packing,
    countdowns,
    events,
    habits,
    home,
    journal,
    portfolio,
    server_stats,
    tasks,
)
from ichrisbirch.config import Settings

logger = logging.getLogger(__name__)


def handle_errors(e, error_code):
    error_title = f'{error_code} {http.HTTPStatus(error_code).phrase}'
    return render_template('error.html', error_title=error_title, error_message=e.description), error_code


def create_app(settings: Settings) -> Flask:
    app = Flask(__name__)
    logger.info('Flask App Created')

    with app.app_context():
        app.config.from_object(settings.flask)
        logger.info('Flask App Configured')
        logger.debug(
            f'DEBUG={app.config.get("DEBUG")}, TESTING={app.config.get("TESTING")}, ENV={app.config.get("ENV")}'
        )

        app.register_error_handler(400, partial(handle_errors, error_code=400))
        app.register_error_handler(404, partial(handle_errors, error_code=404))
        app.register_error_handler(405, partial(handle_errors, error_code=405))
        app.register_error_handler(500, partial(handle_errors, error_code=500))
        app.register_error_handler(502, partial(handle_errors, error_code=502))
        logger.info('Flask App Error Handlers Registered')

        app.register_blueprint(home.blueprint)
        app.register_blueprint(autotasks.blueprint, url_prefix='/autotasks')
        app.register_blueprint(box_packing.blueprint, url_prefix='/box-packing')
        app.register_blueprint(countdowns.blueprint, url_prefix='/countdowns')
        app.register_blueprint(events.blueprint, url_prefix='/events')
        app.register_blueprint(habits.blueprint, url_prefix='/habits')
        app.register_blueprint(server_stats.blueprint, url_prefix='/server_stats')
        app.register_blueprint(journal.blueprint, url_prefix='/journal')
        app.register_blueprint(portfolio.blueprint, url_prefix='/portfolio')
        app.register_blueprint(tasks.blueprint, url_prefix='/tasks')
        logger.info('Flask App Blueprints Registered')
    return app
