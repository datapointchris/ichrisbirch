import logging
from typing import Any

import httpx
import pydantic
from fastapi import status
from flask import Blueprint, Response, flash, render_template, request

from ichrisbirch import schemas
from ichrisbirch.app.helpers import handle_if_not_response_code, url_builder
from ichrisbirch.config import get_settings
from ichrisbirch.models.autotask import TaskFrequency
from ichrisbirch.models.task import TaskCategory

settings = get_settings()
blueprint = Blueprint('autotasks', __name__, template_folder='templates/autotasks', static_folder='static')

logger = logging.getLogger(__name__)

AUTOTASKS_API_URL = f'{settings.api_url}/autotasks/'
TASK_FREQUENCIES = [t.value for t in TaskFrequency]
TASK_CATEGORIES = [t.value for t in TaskCategory]


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data: dict[str, Any] = request.form.to_dict()
        action = data.pop('action')
        logger.debug(f'{request.referrer=} {action=}')
        logger.debug(f'{data=}')

        if action == 'add':
            try:
                autotask = schemas.AutoTaskCreate(**data)
            except pydantic.ValidationError as e:
                logger.exception(e)
                flash(str(e), 'error')
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            response = httpx.post(AUTOTASKS_API_URL, content=autotask.model_dump_json())
            handle_if_not_response_code(201, response, logger)
            new_autotask_run_url = url_builder(AUTOTASKS_API_URL, response.json().get('id'), 'run')
            task_response = httpx.get(new_autotask_run_url)
            handle_if_not_response_code(200, task_response, logger)

        elif action == 'run':
            url = url_builder(AUTOTASKS_API_URL, data.get('id'), 'run')
            response = httpx.get(url)
            handle_if_not_response_code(200, response, logger)

        elif action == 'delete':
            url = url_builder(AUTOTASKS_API_URL, data.get('id'))
            response = httpx.delete(url)
            handle_if_not_response_code(204, response, logger)

        else:
            return Response(f'Method/Action {action} not allowed', status=status.HTTP_405_METHOD_NOT_ALLOWED)

    response = httpx.get(AUTOTASKS_API_URL, follow_redirects=True)
    handle_if_not_response_code(200, response, logger)
    autotasks = [schemas.AutoTask(**task) for task in response.json()]
    return render_template(
        'autotasks/index.html', autotasks=autotasks, task_categories=TASK_CATEGORIES, task_frequencies=TASK_FREQUENCIES
    )
