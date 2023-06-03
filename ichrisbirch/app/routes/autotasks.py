import logging
from typing import Any

import requests
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ichrisbirch import schemas
from ichrisbirch.config import get_settings
from ichrisbirch.models.autotask import TaskFrequency
from ichrisbirch.models.task import TaskCategory

settings = get_settings()
blueprint = Blueprint('autotasks', __name__, template_folder='templates/autotasks', static_folder='static')

logger = logging.getLogger(__name__)

AUTOTASKS_URL = f'{settings.api_url}/autotasks'
TASK_FREQUENCIES = [t.value for t in TaskFrequency]
TASK_CATEGORIES = [t.value for t in TaskCategory]
TIMEOUT = settings.request_timeout


@blueprint.route('/', methods=['GET'])
def index():
    """Autotasks home endpoint"""
    response = requests.get(AUTOTASKS_URL, timeout=TIMEOUT)
    if response.status_code == 200:
        autotasks = [schemas.AutoTask(**task) for task in response.json()]
    else:
        error_message = f'{response.url} : {response.status_code} {response.reason}'
        logger.error(error_message)
        flash(error_message, 'error')
        autotasks = []

    return render_template(
        'autotasks/index.html', autotasks=autotasks, task_categories=TASK_CATEGORIES, task_frequencies=TASK_FREQUENCIES
    )


@blueprint.route('/crud/', methods=['POST'])
def crud():
    """CRUD endpoint for autotasks"""
    data: dict[str, Any] = request.form.to_dict()
    method = data.pop('method')
    logger.debug(f'{request.referrer=}')
    logger.debug(f'{method=}')
    logger.debug(f'{data=}')
    match method:
        case 'add':
            autotask = schemas.AutoTaskCreate(**data).json()
            response = requests.post(AUTOTASKS_URL, data=autotask, timeout=TIMEOUT)
            logger.debug(response.text)
            if response.status_code == 201:
                flash(f'Autotask added: {data.get("name")}', 'success')
            else:
                error_message = f'{response.url} : {response.status_code} {response.reason}'
                logger.error(error_message)
                flash(error_message, 'error')
            return redirect(request.referrer or url_for('autotasks.index'))

        case 'delete':
            autotask_id = data.get('id')
            response = requests.delete(f'{AUTOTASKS_URL}/{autotask_id}', timeout=TIMEOUT)
            logger.debug(response.text)
            if response.status_code == 204:
                flash(f'Autotask deleted: {data.get("name")}', 'success')
            else:
                error_message = f'{response.url} : {response.status_code} {response.reason}'
                logger.error(error_message)
                flash(error_message, 'error')
            return redirect(request.referrer or url_for('autotasks.index'))

    return abort(405, description=f"Method {method} not accepted")
