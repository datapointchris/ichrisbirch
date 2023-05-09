import logging
from typing import Any

import requests
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ichrisbirch import schemas
from ichrisbirch.config import get_settings
from ichrisbirch.models.autotask import TaskFrequency
from ichrisbirch.models.task import TaskCategory

settings = get_settings()
blueprint = Blueprint(
    'autotasks',
    __name__,
    template_folder='templates/autotasks',
    static_folder='static',
)

logger = logging.getLogger(__name__)

AUTOTASKS_URL = f'{settings.api_url}/autotasks'
TASK_FREQUENCIES = [t.value for t in TaskFrequency]
TASK_CATEGORIES = [t.value for t in TaskCategory]
TIMEOUT = settings.request_timeout


@blueprint.route('/', methods=['GET'])
def index():
    """Autotasks home endpoint"""
    try:
        response = requests.get(AUTOTASKS_URL, timeout=TIMEOUT)
        autotasks_json = response.json()
    except Exception as e:
        error_message = f'{__file__}: Error retrieving autotasks from API: {e}'
        logger.error(error_message)
        flash(error_message, 'error')
        autotasks_json = None
    if not autotasks_json:
        autotasks = []
    else:
        autotasks = sorted(
            [schemas.AutoTask(**task) for task in autotasks_json],
            key=lambda x: x.last_run_date,
            reverse=True,
        )
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
    logger.debug(f'{data}')
    match method:
        case 'add':
            try:
                autotask = schemas.AutoTaskCreate(**data).json()
                requests.post(AUTOTASKS_URL, data=autotask, timeout=TIMEOUT)
            except Exception as e:
                error_message = f'Error creating autotask: {e}'
                logger.error(error_message)
                flash(error_message, 'error')
            flash('Autotask created', 'success')
            return redirect(url_for('autotasks.index'))
        case 'delete':
            try:
                autotask_id = data.get('id')
                requests.delete(f'{AUTOTASKS_URL}/{autotask_id}', timeout=TIMEOUT)
            except Exception as e:
                error_message = f'Error deleting autotask: {e}'
                logger.error(error_message)
                flash(error_message, 'error')
            flash('Autotask deleted', 'success')
            return redirect(url_for('autotasks.index'))
    return abort(405, description=f"Method {method} not accepted")
