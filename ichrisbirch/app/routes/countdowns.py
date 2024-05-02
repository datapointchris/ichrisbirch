import logging

from fastapi import status
from flask import Blueprint, Response, render_template, request

from ichrisbirch import schemas
from ichrisbirch.app.query_api import QueryAPI

blueprint = Blueprint('countdowns', __name__, template_folder='templates/countdowns', static_folder='static')
logger = logging.getLogger(__name__)
countdowns_api = QueryAPI(base_url='countdowns', api_key='', logger=logger, response_model=schemas.Countdown)


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.form.to_dict()
        action = data.pop('action')

        match action:
            case 'add':
                countdowns_api.post(data=data)
            case 'delete':
                countdowns_api.delete(data.get('id'))
            case _:
                return Response(f'Method/Action {action} not allowed', status=status.HTTP_405_METHOD_NOT_ALLOWED)

    countdowns = countdowns_api.get()
    return render_template('countdowns/index.html', countdowns=countdowns)
