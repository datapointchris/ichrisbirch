import http
import logging
from functools import partial

from flask import Flask
from flask import render_template
from flask_wtf.csrf import CSRFProtect

from ichrisbirch.app import routes
from ichrisbirch.app.login import login_manager
from ichrisbirch.app.middleware import RequestLoggingMiddleware
from ichrisbirch.config import Settings
from ichrisbirch.util import log_caller

logger = logging.getLogger(__name__)
csrf = CSRFProtect()
request_logger = RequestLoggingMiddleware()


error_codes = [400, 404, 405, 409, 422, 500, 502]


def handle_errors(e, error_code):
    error_title = f'{error_code} {http.HTTPStatus(error_code).phrase}'
    return render_template('error.html', error_title=error_title, error_message=e.description), error_code


@log_caller
def create_app(settings: Settings) -> Flask:
    app = Flask(__name__)
    logger.info('initializing app')
    logger.debug(f'api url: {settings.api_url}')
    logger.debug(f'postgres port: {settings.postgres.port}')
    logger.debug(f'postgres uri: {settings.postgres.db_uri}')
    logger.debug(f'sqlalchemy port: {settings.sqlalchemy.port}')
    logger.debug(f'sqlalchemy uri: {settings.sqlalchemy.db_uri}')

    with app.app_context():
        app.config.from_object(settings.flask)
        logger.info(f'configured from: {type(settings.flask)}')

        cfg = app.config
        logger.debug(f'DEBUG={cfg.get("DEBUG")}, TESTING={cfg.get("TESTING")}, ENV={cfg.get("ENV")}')

        cfg['SETTINGS'] = settings
        logger.info(f'loaded settings: {type(settings)}')

        login_manager.init_app(app)
        logger.info('login manager initialized')

        csrf.init_app(app)
        logger.info('csrf protection initialized')

        request_logger.init_app(app)
        logger.info('request logging middleware initialized')

        for error_code in error_codes:
            app.register_error_handler(error_code, partial(handle_errors, error_code=error_code))
        logger.info('error handlers registered')

        @app.template_filter()
        def pretty_date(dttm, format='%B %d, %Y'):
            return '' if dttm is None else dttm.strftime(format)

        @app.template_filter()
        def pretty_datetime(dttm, format='%B %d, %Y, %I:%M %p'):
            return '' if dttm is None else dttm.strftime(format)

        @app.template_filter()
        def max_length(value, length=80):
            return str(value)[: length - 3] + '...'

        @app.template_filter('currency')
        def currency_filter(value):
            return f'$ {value:,.2f}'

        logger.info('template filters registered')

        app.register_blueprint(routes.home.blueprint)
        app.register_blueprint(routes.auth.blueprint)
        app.register_blueprint(routes.admin.blueprint, url_prefix='/admin')
        app.register_blueprint(routes.articles.blueprint, url_prefix='/articles')
        app.register_blueprint(routes.autotasks.blueprint, url_prefix='/autotasks')
        app.register_blueprint(routes.books.blueprint, url_prefix='/books')
        app.register_blueprint(routes.box_packing.blueprint, url_prefix='/box-packing')
        app.register_blueprint(routes.chat.blueprint, url_prefix='/chat')
        app.register_blueprint(routes.countdowns.blueprint, url_prefix='/countdowns')
        app.register_blueprint(routes.events.blueprint, url_prefix='/events')
        app.register_blueprint(routes.habits.blueprint, url_prefix='/habits')
        app.register_blueprint(routes.journal.blueprint, url_prefix='/journal')
        app.register_blueprint(routes.money_wasted.blueprint, url_prefix='/money-wasted')
        app.register_blueprint(routes.portfolio.blueprint, url_prefix='/portfolio')
        app.register_blueprint(routes.tasks.blueprint, url_prefix='/tasks')
        app.register_blueprint(routes.users.blueprint, url_prefix='/users')
        logger.info('blueprints registered')

        @app.context_processor
        def insert_variables():
            """Must be set on the entire app to be available on every route."""
            return {
                'github_issue_labels_and_icons': [
                    ('bug', 'fa-solid fa-bug'),
                    ('docs', 'fa-solid fa-file-lines'),
                    ('feature', 'fa-regular fa-star'),
                    ('refactor', 'fa-solid fa-code'),
                ],
                'accepting_new_signups': settings.auth.accepting_new_signups,
            }

        @app.context_processor
        def inject_preference_helper():
            """Inject get_user_pref() function into all templates.

            Usage in templates:
                {% set view = get_user_pref('tasks.pages.todo.view_type') %}

            Automatically falls back to DEFAULT_USER_PREFERENCES if key is missing
            from user's preferences. This prevents template crashes when new preference
            keys are added and avoids the need for database migrations.
            """
            from flask_login import current_user

            def get_user_pref(dot_key: str, default=None):
                if current_user.is_authenticated:
                    return current_user.get_preference(dot_key, default)
                return default

            return {'get_user_pref': get_user_pref}

    logger.info('initialized app successfully')
    return app
