import pendulum
import structlog
from fastapi import status
from flask import Blueprint
from flask import abort
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.client.exceptions import APIHTTPError
from ichrisbirch.api.client.logging_client import logging_internal_service_client
from ichrisbirch.app import forms
from ichrisbirch.app.utils import http as http_utils

logger = structlog.get_logger()
blueprint = Blueprint('auth', __name__, template_folder='templates/auth', static_folder='static')


@blueprint.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash(f'logged in as: {current_user.name}', 'success')
        return redirect(request.referrer or url_for('users.profile'))
    form = forms.LoginForm()
    if form.validate_on_submit():
        # Get the API URL from Flask app's settings (for testing compatibility)
        api_url = current_app.config['SETTINGS'].api_url
        # Use new internal service client instead of service account
        with logging_internal_service_client(base_url=api_url) as client:
            users = client.resource('users', schemas.User)
            try:
                user_data = users.get_generic(['email', form.email.data])
            except APIHTTPError as e:
                if e.status_code == 404:
                    user_data = None
                else:
                    raise
            if user_data:
                user = models.User(**user_data)
                if user and user.check_password(password=form.password.data):
                    login_user(user, remember=form.remember_me.data)
                    logger.info('user_login_success', name=user.name, last_login=str(user.last_login))
                    try:
                        users.patch([user.id], json={'last_login': pendulum.now().for_json()})
                        logger.debug('user_last_login_updated', name=user.name)
                    except Exception as e:
                        # Silent failure: last_login update is non-critical
                        # User cannot act on this, don't block login or show error
                        # System log captures issue for debugging
                        logger.error('user_last_login_update_error', name=user.name, error=str(e))
                    if next_page := session.get('next'):
                        logger.debug('login_redirect_from_session', next_page=next_page)
                    else:
                        logger.debug('login_redirect_default')
                        next_page = url_for('users.profile')
                    logger.debug('login_redirecting', next_page=next_page)
                    if not http_utils.url_has_allowed_host_and_scheme(next_page, request.host):
                        return abort(status.HTTP_401_UNAUTHORIZED, f'Unauthorized URL: {next_page}')
                    return redirect(next_page)
                else:
                    logger.warning('login_failed_invalid_password', email=form.email.data)
            else:
                logger.warning('login_failed_user_not_found', email=form.email.data)

        logout_user()
        flash('Invalid credentials', 'error')
        # TODO: [2024/05/21] - add a login attempt counter, possibly using redis or something similar
        return redirect(url_for('auth.login'))

    return render_template('auth/login.html', form=form, template='login-page')


@blueprint.route('/signup/', methods=['GET', 'POST'])
def signup():
    settings = current_app.config['SETTINGS']
    if not settings.auth.accepting_new_signups:
        flash(settings.auth.no_new_signups_message, 'error')
        return redirect(url_for('home.index'))

    # Get the API URL from Flask app's settings (for testing compatibility)
    api_url = current_app.config['SETTINGS'].api_url
    # Use new internal service client instead of service account
    with logging_internal_service_client(base_url=api_url) as client:
        users = client.resource('users', schemas.User)
        form = forms.SignupForm()
        if form.validate_on_submit():
            logger.debug('signup_form_validated')
            logger.debug('signup_checking_existing_user')
            try:
                existing_user = users.get_generic(['email', form.email.data])
            except APIHTTPError as e:
                if e.status_code == 404:
                    existing_user = None
                else:
                    raise
            if not existing_user:
                logger.info('user_creating', email=form.email.data)
                data = {
                    'name': form.name.data,
                    'email': form.email.data,
                    'password': form.password.data,
                }
                if new_user := users.post(json=data):
                    user = models.User(**new_user.model_dump())
                    login_user(user)
                    return redirect(url_for('users.profile'))
                return redirect(url_for('auth.signup'))
            else:
                logger.warning('signup_duplicate_email', email=form.email.data, last_login=existing_user.get('last_login', 'unknown'))
                flash('email address already registered', 'error')
        else:
            if request.method.upper() == 'POST':
                logger.warning('signup_form_validation_failed', errors=form.errors)

        return render_template(
            'auth/signup.html',
            title='Create an Account.',
            form=form,
            template='signup-page',
            body='Sign up for a user account.',
        )


@blueprint.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home.index'))
