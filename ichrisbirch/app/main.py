import http
from contextlib import suppress
from functools import partial

import structlog
from flask import Flask
from flask import render_template
from flask import request
from flask_login import current_user
from flask_wtf.csrf import CSRFProtect

from ichrisbirch.app import routes
from ichrisbirch.app.login import login_manager
from ichrisbirch.app.middleware import RequestLoggingMiddleware
from ichrisbirch.config import Settings
from ichrisbirch.util import log_caller

logger = structlog.get_logger()
csrf = CSRFProtect()
request_logger = RequestLoggingMiddleware()


error_codes = [400, 404, 405, 409, 422, 500, 502]


def _get_user_id() -> str:
    """Get current user ID for logging, handling unauthenticated users."""
    with suppress(RuntimeError):
        if current_user.is_authenticated:
            return str(current_user.id)
    return 'anonymous'


def handle_errors(e, error_code):
    """Handle HTTP errors with logging."""
    user_id = _get_user_id()
    description = getattr(e, 'description', str(e))
    if error_code >= 500:
        logger.error('http_error', status=error_code, method=request.method, path=request.path, user_id=user_id, error=description)
    else:
        logger.warning('http_error', status=error_code, method=request.method, path=request.path, user_id=user_id, error=description)
    error_title = f'{error_code} {http.HTTPStatus(error_code).phrase}'
    return render_template('error.html', error_title=error_title, error_message=description), error_code


def handle_exception(e):
    """Handle unhandled exceptions with logging."""
    user_id = _get_user_id()
    logger.error(
        'unhandled_exception',
        method=request.method,
        path=request.path,
        user_id=user_id,
        error=str(e),
        error_type=type(e).__name__,
    )
    error_title = '500 Internal Server Error'
    return render_template('error.html', error_title=error_title, error_message='An unexpected error occurred'), 500


@log_caller
def create_app(settings: Settings) -> Flask:
    app = Flask(__name__)
    logger.info('app_initializing')
    logger.debug('api_config', api_url=settings.api_url)
    logger.debug('postgres_config', port=settings.postgres.port, uri=settings.postgres.db_uri)
    logger.debug('sqlalchemy_config', port=settings.sqlalchemy.port, uri=settings.sqlalchemy.db_uri)

    with app.app_context():
        app.config.from_object(settings.flask)
        logger.info('config_loaded', settings_type=type(settings.flask).__name__)

        cfg = app.config
        logger.debug('flask_config', debug=cfg.get('DEBUG'), testing=cfg.get('TESTING'), env=cfg.get('ENV'))

        cfg['SETTINGS'] = settings
        logger.info('settings_loaded', settings_type=type(settings).__name__)

        login_manager.init_app(app)
        logger.info('login_manager_initialized')

        csrf.init_app(app)
        logger.info('csrf_initialized')

        request_logger.init_app(app)
        logger.info('request_logging_initialized')

        for error_code in error_codes:
            app.register_error_handler(error_code, partial(handle_errors, error_code=error_code))
        app.register_error_handler(Exception, handle_exception)
        logger.info('error_handlers_registered')

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

        logger.info('template_filters_registered')

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
        logger.info('blueprints_registered')

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

    logger.info('app_initialized')
    return app
