import logging
from typing import Any

import requests
from fastapi import status
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
    if response.status_code == status.HTTP_200_OK:
        autotasks = [schemas.AutoTask(**task) for task in response.json()]
    else:
        error_message = f'{response.url} : {response.status_code} {response.reason}'
        logger.error(error_message)
        logger.error(response.text)
        flash(error_message, 'error')
        flash(response.text, 'error')
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
            autotask = schemas.AutoTaskCreate(**data)
            response = requests.post(AUTOTASKS_URL, data=autotask.json(), timeout=TIMEOUT)
            if response.status_code != status.HTTP_201_CREATED:
                error_message = f'{response.url} : {response.status_code} {response.reason}'
                logger.error(error_message)
                logger.error(response.text)
                flash(error_message, 'error')
                flash(response.text, 'error')
            else:  # Run the new autotask
                task_response = requests.get(f'{AUTOTASKS_URL}/{response.json().get("id")}/run/', timeout=TIMEOUT)
                if task_response.status_code != status.HTTP_200_OK:
                    error_message = f'{response.url} : {response.status_code} {response.reason}'
                    logger.error(error_message)
                    logger.error(response.text)
                    flash(error_message, 'error')
                    flash(response.text, 'error')
            return redirect(request.referrer or url_for('autotasks.index'))

        case 'delete':
            autotask_id = data.get('id')
            response = requests.delete(f'{AUTOTASKS_URL}/{autotask_id}/', timeout=TIMEOUT)
            if response.status_code != status.HTTP_204_NO_CONTENT:
                error_message = f'{response.url} : {response.status_code} {response.reason}'
                logger.error(error_message)
                logger.error(response.text)
                flash(error_message, 'error')
                flash(response.text, 'error')
            return redirect(request.referrer or url_for('autotasks.index'))

        case 'run':
            autotask_id = data.get('id')
            response = requests.get(f'{AUTOTASKS_URL}/{autotask_id}/run/', timeout=TIMEOUT)
            if response.status_code != status.HTTP_200_OK:
                error_message = f'{response.url} : {response.status_code} {response.reason}'
                logger.error(error_message)
                logger.error(response.text)
                flash(error_message, 'error')
                flash(response.text, 'error')
            return redirect(request.referrer or url_for('autotasks.index'))

    return abort(status.HTTP_405_METHOD_NOT_ALLOWED, description=f"Method {method} not accepted")
