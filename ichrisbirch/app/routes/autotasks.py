import logging
from typing import Any

import requests
from flask import Blueprint, abort, redirect, render_template, request, url_for

from ichrisbirch import schemas
from ichrisbirch.config import settings
from ichrisbirch.models.autotask import TaskFrequency

blueprint = Blueprint(
    'autotasks',
    __name__,
    template_folder='templates/autotasks',
    static_folder='static',
)

logger = logging.getLogger(__name__)

AUTOTASKS_URL = f'{settings.api_url}/autotasks'
TASK_FREQUENCIES = [t.value for t in TaskFrequency]
TIMEOUT = settings.request_timeout


@blueprint.route('/', methods=['GET'])
def index():
    """Autotasks home endpoint"""
    return render_template(
        'autotasks/index.html',
        autotasks=sorted(
            [schemas.AutoTask(**task) for task in requests.get(AUTOTASKS_URL, timeout=TIMEOUT).json()],
            key=lambda x: x.last_run_date,
            reverse=True,
        ),
        task_frequencies=TASK_FREQUENCIES,
    )


@blueprint.route('/crud/', methods=['POST'])
def crud():
    """CRUD endpoint for autotasks"""
    data: dict[str, Any] = request.form.to_dict()
    method = data.pop('method')
    logger.debug(f'{request.referrer=}')
    logger.debug(f'{method=}')
    logger.debug(f'{data}')
    match method:
        case 'add':
            autotask = schemas.AutoTaskCreate(**data).json()
            response = requests.post(AUTOTASKS_URL, data=autotask, timeout=TIMEOUT)
            logger.debug(response.text)
            return redirect(url_for('autotasks.index'))
        case 'delete':
            autotask_id = data.get('id')
            response = requests.delete(f'{AUTOTASKS_URL}/{autotask_id}', timeout=TIMEOUT)
            logger.debug(response.text)
            return redirect(url_for('autotasks.index'))
    return abort(405, description=f"Method {method} not accepted")
