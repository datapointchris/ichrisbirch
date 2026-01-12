import logging

import pendulum
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

logger = logging.getLogger(__name__)
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
                    logger.debug(f'logged in user: {user.name} - last previous login: {user.last_login}')
                    try:
                        # Update last login using the same client
                        users.patch([user.id], json={'last_login': pendulum.now().for_json()})
                        logger.debug(f'updated last login for user: {user.name}')
                    except Exception as e:
                        logger.error(f'error updating last login for user {user.name}: {e}')
                    if next_page := session.get('next'):
                        logger.debug(f'next page stored in session: {next_page}')
                    else:
                        logger.debug('session["next"] was not set')
                        next_page = url_for('users.profile')
                    logger.debug(f'login will redirect to: {next_page}')
                    if not http_utils.url_has_allowed_host_and_scheme(next_page, request.host):
                        return abort(status.HTTP_401_UNAUTHORIZED, f'Unauthorized URL: {next_page}')
                    return redirect(next_page)
                else:
                    logger.warning(f'failed login attempt for user: {form.email.data} - invalid password')
            else:
                logger.warning(f'failed login attempt - no user found for email: {form.email.data}')

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
            logger.debug('signup form validated')
            logger.debug('checking for existing user')
            try:
                existing_user = users.get_generic(['email', form.email.data])
            except APIHTTPError as e:
                if e.status_code == 404:
                    existing_user = None
                else:
                    raise
            if not existing_user:
                logger.info(f'creating a new user with email: {form.email.data}')
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
                logger.warning(
                    f'duplicate email registration attempt: {form.email.data} - last login: {existing_user.get("last_login", "unknown")}'
                )
                flash('email address already registered', 'error')
        else:
            if request.method.upper() == 'POST':
                logger.warning(f'form validation failed: {form.errors}')

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
