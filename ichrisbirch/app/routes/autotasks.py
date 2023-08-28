import logging
from typing import Any

import pydantic
import requests
from fastapi import status
from flask import Blueprint, Response, flash, render_template, request

from ichrisbirch import schemas
from ichrisbirch.app.helpers import log_flash_raise_error
from ichrisbirch.config import get_settings
from ichrisbirch.models.autotask import TaskFrequency
from ichrisbirch.models.task import TaskCategory

settings = get_settings()
blueprint = Blueprint('autotasks', __name__, template_folder='templates/autotasks', static_folder='static')

logger = logging.getLogger(__name__)

AUTOTASKS_API_URL = f'{settings.api_url}/autotasks'
TASK_FREQUENCIES = [t.value for t in TaskFrequency]
TASK_CATEGORIES = [t.value for t in TaskCategory]
TIMEOUT = settings.request_timeout


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data: dict[str, Any] = request.form.to_dict()
        method = data.pop('method')
        logger.debug(f'{request.referrer=} | {method=} | {data=}')
        match method:
            case 'add':
                try:
                    autotask = schemas.AutoTaskCreate(**data)
                except pydantic.ValidationError as e:
                    logger.exception(e)
                    flash(str(e), 'error')
                    return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
                response = requests.post(AUTOTASKS_API_URL, data=autotask.json(), timeout=TIMEOUT)
                if response.status_code != status.HTTP_201_CREATED:
                    log_flash_raise_error(response, logger)
                else:  # Run the new autotask
                    task_response = requests.get(
                        f'{AUTOTASKS_API_URL}/{response.json().get("id")}/run/', timeout=TIMEOUT
                    )
                    if task_response.status_code != status.HTTP_200_OK:
                        log_flash_raise_error(task_response, logger)

            case 'run':
                id = request.form.get('id')
                response = requests.get(f'{AUTOTASKS_API_URL}/{id}/run/', timeout=TIMEOUT)
                if response.status_code != status.HTTP_200_OK:
                    log_flash_raise_error(response, logger)

            case 'delete':
                autotask_id = data.get('id')
                response = requests.delete(f'{AUTOTASKS_API_URL}/{autotask_id}/', timeout=TIMEOUT)
                if response.status_code != status.HTTP_204_NO_CONTENT:
                    log_flash_raise_error(response, logger)

            case _:
                return Response(f'Method {method} not allowed', status=status.HTTP_405_METHOD_NOT_ALLOWED)

    response = requests.get(AUTOTASKS_API_URL, timeout=TIMEOUT)
    if response.status_code == status.HTTP_200_OK:
        log_flash_raise_error(response, logger)
    autotasks = [schemas.AutoTask(**task) for task in response.json()]
    return render_template(
        'autotasks/index.html', autotasks=autotasks, task_categories=TASK_CATEGORIES, task_frequencies=TASK_FREQUENCIES
    )
