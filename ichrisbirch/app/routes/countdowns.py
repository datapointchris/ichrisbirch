import logging

from fastapi import status
from flask import Blueprint
from flask import Response
from flask import render_template
from flask import request

from ichrisbirch import schemas
from ichrisbirch.app.query_api import QueryAPI

logger = logging.getLogger('app.countdowns')
blueprint = Blueprint('countdowns', __name__, template_folder='templates/countdowns', static_folder='static')
countdowns_api = QueryAPI(base_url='countdowns', logger=logger, response_model=schemas.Countdown)


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
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
