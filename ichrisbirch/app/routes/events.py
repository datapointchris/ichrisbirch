import logging
from datetime import datetime

from fastapi import status
from flask import Blueprint
from flask import Response
from flask import render_template
from flask import request

from ichrisbirch import schemas
from ichrisbirch.app.query_api import QueryAPI

LOCAL_TZ = datetime.now().astimezone().tzinfo

blueprint = Blueprint('events', __name__, template_folder='templates/events', static_folder='static')
logger = logging.getLogger(__name__)
events_api = QueryAPI(base_url='events', api_key='', logger=logger, response_model=schemas.Event)


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.form.to_dict()
        action = data.pop('action')

        match action:
            case 'add':
                # add local timezone if one isn't provided
                if not datetime.fromisoformat(data['date']).tzname:
                    data['date'] = datetime.fromisoformat(data['date']).replace(tzinfo=LOCAL_TZ).isoformat()
                events_api.post(data=data)
            case 'delete':
                events_api.delete(data.get('id'))
            case 'attend':
                events_api.patch([data.get('id'), 'attend'])
            case _:
                return Response(f'Method/Action {action} not allowed', status=status.HTTP_405_METHOD_NOT_ALLOWED)

    events = events_api.get()
    return render_template('events/index.html', events=events)
