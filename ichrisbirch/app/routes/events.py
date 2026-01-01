import logging
from datetime import datetime

import pendulum
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
blueprint = Blueprint('events', __name__, template_folder='templates/events', static_folder='static')


@blueprint.before_request
@login_required
def enforce_login():
    pass


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    settings = current_app.config['SETTINGS']
    TZ = pendulum.timezone(settings.global_timezone)
    with logging_flask_session_client(base_url=settings.api_url) as client:
        events_api = client.resource('events', schemas.Event)
        if request.method.upper() == 'POST':
            data = request.form.to_dict()
            action = data.pop('action')

            match action:
                case 'add':
                    # add local timezone if one isn't provided
                    if not datetime.fromisoformat(data['date']).tzname:
                        data['date'] = TZ.convert(datetime.fromisoformat(data['date'])).isoformat()
                    events_api.post(json=data)
                case 'delete':
                    events_api.delete(data.get('id'))
                case 'attend':
                    events_api.patch([data.get('id'), 'attend'])
                case _:
                    return Response(f'Method/Action {action} not allowed', status=status.HTTP_405_METHOD_NOT_ALLOWED)

        events = events_api.get_many()
        return render_template('events/index.html', events=events)
