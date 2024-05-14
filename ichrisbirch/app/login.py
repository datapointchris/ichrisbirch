import logging

from flask import flash
from flask import redirect
from flask import url_for
from flask_login import LoginManager

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.app.query_api import QueryAPI

logger = logging.getLogger('app.login_manager')
login_manager = LoginManager()
user_api = QueryAPI(base_url='users', api_key='', logger=logger, response_model=schemas.User)


@login_manager.user_loader
def load_user(alternative_id):
    """Reload the user object from the user ID stored in the session.

    Must return the User object or None Using the user ID as the value of the remember token means you must change the
    user ID to invalidate their login sessions. One way to improve this is to use an alternative user id instead of the
    user ID.
    """
    user_response = user_api.get_one(['alt', alternative_id])
    return models.User(**user_response.model_dump())


@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to Login page."""
    flash('You must be logged in to view that page.')
    return redirect(url_for('auth.login'))
