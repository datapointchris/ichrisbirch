import structlog
from flask import Blueprint
from flask import current_app
from flask import redirect
from flask import render_template
from flask import request
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
    return render_template('users/settings.html', user=current_user)


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
