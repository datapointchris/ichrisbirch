import logging

from fastapi import status
from flask import Blueprint
from flask import Response
from flask import render_template
from flask import request
from flask_login import login_required

from ichrisbirch import schemas
from ichrisbirch.app.query_api import QueryAPI
from ichrisbirch.models.autotask import AutoTaskFrequency
from ichrisbirch.models.task import TaskCategory

AUTOTASK_FREQUENCIES = [t.value for t in AutoTaskFrequency]
TASK_CATEGORIES = [t.value for t in TaskCategory]

logger = logging.getLogger('app.autotasks')
blueprint = Blueprint('autotasks', __name__, template_folder='templates/autotasks', static_folder='static')


@blueprint.before_request
@login_required
def enforce_login():
    pass


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    autotasks_api = QueryAPI(base_endpoint='autotasks', response_model=schemas.AutoTask)
    if request.method.upper() == 'POST':
        data = request.form.to_dict()
        action = data.pop('action')

        match action:
            case 'add':
                created = autotasks_api.post(json=data)
                autotasks_api.patch([created.id, 'run'])
            case 'run':
                autotasks_api.patch([data.get('id'), 'run'])
            case 'delete':
                autotasks_api.delete(data.get('id'))
            case _:
                return Response(f'Method/Action {action} not allowed', status=status.HTTP_405_METHOD_NOT_ALLOWED)

    autotasks = autotasks_api.get_many()
    return render_template(
        'autotasks/index.html',
        autotasks=autotasks,
        task_categories=TASK_CATEGORIES,
        autotask_frequencies=AUTOTASK_FREQUENCIES,
    )
