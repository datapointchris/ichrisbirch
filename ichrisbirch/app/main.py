import http
import logging
from functools import partial

from flask import Flask
from flask import g
from flask import render_template

from ichrisbirch.app import routes
from ichrisbirch.app.login import login_manager
from ichrisbirch.config import Settings

logger = logging.getLogger('app')


def handle_errors(e, error_code):
    error_title = f'{error_code} {http.HTTPStatus(error_code).phrase}'
    return render_template('error.html', error_title=error_title, error_message=e.description), error_code


def create_app(settings: Settings) -> Flask:
    app = Flask(__name__)
    logger.info('created')

    login_manager.init_app(app)
    logger.info('login manager initialized')

    with app.app_context():
        app.config.from_object(settings.flask)
        logger.info('configured')
        logger.debug(
            f'DEBUG={app.config.get("DEBUG")}, TESTING={app.config.get("TESTING")}, ENV={app.config.get("ENV")}'
        )

        app.register_error_handler(400, partial(handle_errors, error_code=400))
        app.register_error_handler(404, partial(handle_errors, error_code=404))
        app.register_error_handler(405, partial(handle_errors, error_code=405))
        app.register_error_handler(422, partial(handle_errors, error_code=422))
        app.register_error_handler(500, partial(handle_errors, error_code=500))
        app.register_error_handler(502, partial(handle_errors, error_code=502))
        logger.info('error handlers registered')

        @app.template_filter()
        def pretty_date(dttm, format='%B %d, %Y'):
            return '' if dttm is None else dttm.strftime(format)

        logger.info('template filters registered')

        app.register_blueprint(routes.home.blueprint)
        app.register_blueprint(routes.auth.blueprint)
        app.register_blueprint(routes.autotasks.blueprint, url_prefix='/autotasks')
        app.register_blueprint(routes.box_packing.blueprint, url_prefix='/box-packing')
        app.register_blueprint(routes.countdowns.blueprint, url_prefix='/countdowns')
        app.register_blueprint(routes.events.blueprint, url_prefix='/events')
        app.register_blueprint(routes.habits.blueprint, url_prefix='/habits')
        app.register_blueprint(routes.journal.blueprint, url_prefix='/journal')
        app.register_blueprint(routes.portfolio.blueprint, url_prefix='/portfolio')
        app.register_blueprint(routes.tasks.blueprint, url_prefix='/tasks')
        app.register_blueprint(routes.users.blueprint, url_prefix='/users')
        logger.info('blueprints registered')

        # TODO: [2024/05/03] - Database Initialization

        @app.before_request
        def repo_labels_and_icons():
            """Must be set on the entire app to be available on every route."""
            g.github_issue_labels_and_icons = [
                ('bug', 'fa-solid fa-bug'),
                ('docs', 'fa-solid fa-file-lines'),
                ('feature', 'fa-regular fa-star'),
                ('refactor', 'fa-solid fa-code'),
            ]

    return app
