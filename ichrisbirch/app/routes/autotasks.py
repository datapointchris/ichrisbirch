import logging

from fastapi import status
from flask import Blueprint
from flask import Response
from flask import render_template
from flask import request

from ichrisbirch import schemas
from ichrisbirch.app.query_api import QueryAPI
from ichrisbirch.models.autotask import TaskFrequency
from ichrisbirch.models.task import TaskCategory

TASK_FREQUENCIES = [t.value for t in TaskFrequency]
TASK_CATEGORIES = [t.value for t in TaskCategory]

blueprint = Blueprint('autotasks', __name__, template_folder='templates/autotasks', static_folder='static')
logger = logging.getLogger(__name__)
autotasks_api = QueryAPI(base_url='autotasks', api_key='', logger=logger, response_model=schemas.AutoTask)


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.form.to_dict()
        action = data.pop('action')

        match action:
            case 'add':
                created = autotasks_api.post(data=data)
                autotasks_api.patch([created.id, 'run'])
            case 'run':
                autotasks_api.patch([data.get('id'), 'run'])
            case 'delete':
                autotasks_api.delete(data.get('id'))
            case _:
                return Response(f'Method/Action {action} not allowed', status=status.HTTP_405_METHOD_NOT_ALLOWED)

    autotasks = autotasks_api.get()
    return render_template(
        'autotasks/index.html', autotasks=autotasks, task_categories=TASK_CATEGORIES, task_frequencies=TASK_FREQUENCIES
    )
