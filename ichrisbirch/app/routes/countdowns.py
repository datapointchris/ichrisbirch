import logging
from typing import Any

import httpx
import pydantic
from fastapi import status
from flask import Blueprint, Response, flash, redirect, render_template, request, url_for

from ichrisbirch import schemas
from ichrisbirch.app.helpers import handle_if_not_response_code, url_builder
from ichrisbirch.config import get_settings

settings = get_settings()
blueprint = Blueprint('countdowns', __name__, template_folder='templates/countdowns', static_folder='static')

logger = logging.getLogger(__name__)

COUNTDOWNS_API_URL = f'{settings.api_url}/countdowns/'


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data: dict[str, Any] = request.form.to_dict()
        action = data.pop('action')
        logger.debug(f'{request.referrer=} {action=}')
        logger.debug(f'{data=}')

        if action == 'add':
            try:
                countdown = schemas.CountdownCreate(**data).model_dump_json()
            except pydantic.ValidationError as e:
                logger.exception(e)
                flash(str(e), 'error')
                return redirect(request.referrer or url_for('countdowns.index'))
            response = httpx.post(COUNTDOWNS_API_URL, content=countdown)
            handle_if_not_response_code(201, response, logger)

        elif action == 'delete':
            url = url_builder(COUNTDOWNS_API_URL, data.get('id'))
            response = httpx.delete(url)
            handle_if_not_response_code(204, response, logger)

        else:
            return Response(f'Method/Action {action} not allowed', status=status.HTTP_405_METHOD_NOT_ALLOWED)

    response = httpx.get(COUNTDOWNS_API_URL)
    handle_if_not_response_code(200, response, logger)
    countdowns = [schemas.Countdown(**countdown) for countdown in response.json()]
    return render_template('countdowns/index.html', countdowns=countdowns)
