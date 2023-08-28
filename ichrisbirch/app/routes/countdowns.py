import logging
from typing import Any

import pydantic
import requests
from fastapi import status
from flask import Blueprint, Response, flash, render_template, request

from ichrisbirch import schemas
from ichrisbirch.app.helpers import log_flash_raise_error
from ichrisbirch.config import get_settings

settings = get_settings()
blueprint = Blueprint('countdowns', __name__, template_folder='templates/countdowns', static_folder='static')

logger = logging.getLogger(__name__)

COUNTDOWNS_API_URL = f'{settings.api_url}/countdowns'
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
                    countdown = schemas.CountdownCreate(**data).json()
                except pydantic.ValidationError as e:
                    logger.exception(e)
                    flash(str(e), 'error')
                    return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
                response = requests.post(COUNTDOWNS_API_URL, data=countdown, timeout=TIMEOUT)
                if response.status_code != status.HTTP_201_CREATED:
                    log_flash_raise_error(response, logger)

            case 'delete':
                id = data.get('id')
                response = requests.delete(f'{COUNTDOWNS_API_URL}/{id}', timeout=TIMEOUT)
                if response.status_code != status.HTTP_204_NO_CONTENT:
                    log_flash_raise_error(response, logger)
            case _:
                return Response(f'Method {method} not allowed', status=status.HTTP_405_METHOD_NOT_ALLOWED)

    response = requests.get(COUNTDOWNS_API_URL, timeout=TIMEOUT)
    if response.status_code != status.HTTP_200_OK:
        log_flash_raise_error(response, logger)
    countdowns = [schemas.Countdown(**countdown) for countdown in response.json()]
    return render_template('countdowns/index.html', countdowns=countdowns)
