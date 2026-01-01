import logging

from fastapi import status
from flask import Blueprint
from flask import Response
from flask import current_app
from flask import render_template
from flask import request
from flask_login import login_required

from ichrisbirch import schemas
from ichrisbirch.api.client.logging_client import logging_flask_session_client

logger = logging.getLogger(__name__)
blueprint = Blueprint('countdowns', __name__, template_folder='templates/countdowns', static_folder='static')


@blueprint.before_request
@login_required
def enforce_login():
    pass


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    base_url = current_app.config['SETTINGS'].api_url
    with logging_flask_session_client(base_url=base_url) as client:
        countdowns_api = client.resource('countdowns', schemas.Countdown)
        if request.method.upper() == 'POST':
            data = request.form.to_dict()
            action = data.pop('action')

            match action:
                case 'add':
                    countdowns_api.post(json=data)
                case 'delete':
                    countdowns_api.delete(data.get('id'))
                case _:
                    return Response(f'Method/Action {action} not allowed', status=status.HTTP_405_METHOD_NOT_ALLOWED)

        countdowns = countdowns_api.get_many()
        return render_template('countdowns/index.html', countdowns=countdowns)
