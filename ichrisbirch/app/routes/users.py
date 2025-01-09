import logging

from fastapi import status
from flask import Blueprint
from flask import Response
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
def preferences():
    users_api = QueryAPI(base_url='users', user='', logger=logger, response_model=schemas.User)

    data = request.form.to_dict()
    action = data.pop('action')

    match action:
        case 'toggle_box_packing_compact_view':
            toggle = not current_user.preferences['box_packing']['compact_view']
            users_api.patch('/me/preferences/', json={'box_packing': {'compact_view': toggle}})
            return redirect(request.referrer)

    return Response(f'Method/Action {action} not accepted', status=status.HTTP_405_METHOD_NOT_ALLOWED)
