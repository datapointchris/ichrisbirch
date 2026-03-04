import structlog
from flask import Blueprint
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import fresh_login_required
from flask_login import login_required

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.client.logging_client import logging_flask_session_client

logger = structlog.get_logger()
blueprint = Blueprint('users', __name__, template_folder='templates/users', static_folder='static')


@blueprint.route('/profile/', methods=['GET'])
@login_required
def profile():
    return render_template('users/profile.html', user=current_user)


@blueprint.route('/update/', methods=['GET', 'POST'])
@fresh_login_required
def update():
    return render_template('users/update.html', user=current_user)


@blueprint.route('/settings/', methods=['GET', 'POST'])
@fresh_login_required
def settings():
    base_url = current_app.config['SETTINGS'].api_url
    api_keys = []
    with logging_flask_session_client(base_url=base_url) as client:
        keys_api = client.resource('api-keys', schemas.PersonalAPIKey)
        api_keys = keys_api.get_many()
    return render_template('users/settings.html', user=current_user, api_keys=api_keys)


@blueprint.route('/api-keys/create/', methods=['POST'])
@fresh_login_required
def create_api_key():
    base_url = current_app.config['SETTINGS'].api_url
    name = request.form.get('name', 'Unnamed Key')
    with logging_flask_session_client(base_url=base_url) as client:
        keys_api = client.resource('api-keys', schemas.PersonalAPIKeyCreated)
        result = keys_api.post(json={'name': name})
        if result:
            flash(f'API key created. Copy it now — it will not be shown again: {result.key}', 'success')
        else:
            flash('Failed to create API key.', 'error')
    return redirect(url_for('users.settings'))


@blueprint.route('/api-keys/<int:key_id>/revoke/', methods=['POST'])
@fresh_login_required
def revoke_api_key(key_id):
    base_url = current_app.config['SETTINGS'].api_url
    with logging_flask_session_client(base_url=base_url) as client:
        keys_api = client.resource('api-keys', schemas.PersonalAPIKey)
        keys_api.delete(f'{key_id}/')
        flash('API key revoked.', 'success')
    return redirect(url_for('users.settings'))


@blueprint.route('/preferences/', methods=['POST'])
@login_required
def preferences():
    base_url = current_app.config['SETTINGS'].api_url
    with logging_flask_session_client(base_url=base_url) as client:
        users_api = client.resource('users', schemas.User)
        data = request.form.to_dict()
        payload = models.User.dot_preference_to_nested_dict(data['preference-key'], data['preference-value'])
        users_api.patch('/me/preferences/', json=payload)
        return redirect(request.referrer)
