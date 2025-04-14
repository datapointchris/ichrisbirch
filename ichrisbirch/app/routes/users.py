import logging
from typing import Any

from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask_login import current_user
from flask_login import fresh_login_required
from flask_login import login_required

from ichrisbirch import schemas
from ichrisbirch.app.query_api import QueryAPI

logger = logging.getLogger('app.users')
blueprint = Blueprint('users', __name__, template_folder='templates/users', static_folder='static')


def _convert_dot_separated_prefernce_to_nested_dict(dot_key: str, value: Any) -> dict:
    """Create a nested dictionary from a dot-separated key.

    Preference keys come in like:
        `preference.app.sub_pref.key`
    Convert to a nested dictionary compatible with User.preferences in order to store in the database as JSONB.
    """
    keys = dot_key.split('.')
    nested_dict = value
    for key in reversed(keys):
        nested_dict = {key: nested_dict}
    return nested_dict


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
    users_api = QueryAPI(base_url='users', response_model=schemas.User)
    data = request.form.to_dict()
    payload = _convert_dot_separated_prefernce_to_nested_dict(data['preference'], data['value'])
    users_api.patch('/me/preferences/', json=payload)
    return redirect(request.referrer)
