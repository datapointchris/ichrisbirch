from contextlib import suppress
from functools import wraps

import structlog
from flask import current_app
from flask import request
from flask_login import LoginManager
from flask_login import current_user
from flask_login.config import EXEMPT_METHODS

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.client.exceptions import APIClientError
from ichrisbirch.api.client.logging_client import logging_internal_service_client

logger = structlog.get_logger()


def get_users_api():
    """Get users API client using modern internal service authentication."""
    with suppress(RuntimeError):
        if current_app and 'SETTINGS' in current_app.config:
            api_url = current_app.config['SETTINGS'].api_url
            return logging_internal_service_client(base_url=api_url)
    return logging_internal_service_client()


login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'You must be logged in to view that page'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(alternative_id):
    """Reload the user object from the user ID stored in the session.

    Must return the User object or None. Using the user ID as the value of the remember token means you must change
    the user ID to invalidate their login sessions. One way to improve this is to use an alternative user id instead
    of the user ID.

    Returns None if user not found or API unreachable, which triggers Flask-Login to treat the session as invalid
    and redirect to login.
    """
    try:
        with get_users_api() as client:
            users = client.resource('users', schemas.User)
            if user_data := users.get_generic(['alt', alternative_id]):
                user = models.User(**user_data)
                logger.debug('user_loaded', alternative_id=user.alternative_id, email=user.email)
                return user
    except APIClientError as e:
        logger.warning('user_load_failed', alternative_id=alternative_id, error=str(e))
    return None


def admin_login_required(func):
    """A version of `login_required` from `flask-login`
    https://github.com/maxcountryman/flask-login/blob/529be4b5f49075500010811d6c739e85e02b9c2e/src/flask_login/utils.py#L246
    This decorator requires both the user is logged in and also the user is an admin
    """

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if request.method in EXEMPT_METHODS or current_app.config.get('LOGIN_DISABLED'):
            return func(*args, **kwargs)
        if not (current_user.is_authenticated and current_user.is_admin):
            return current_app.login_manager.unauthorized()
        return func(*args, **kwargs)

    return decorated_view
