import logging
from datetime import datetime
from typing import Any

import requests
from fastapi import status
from fastapi.encoders import jsonable_encoder
from flask import Blueprint, Response, render_template, request

from ichrisbirch import schemas
from ichrisbirch.app.helpers import log_flash_raise_error
from ichrisbirch.config import get_settings

settings = get_settings()
blueprint = Blueprint('events', __name__, template_folder='templates/events', static_folder='static')

logger = logging.getLogger(__name__)

EVENTS_API_URL = f'{settings.api_url}/events'
TIMEOUT = settings.request_timeout
LOCAL_TZ = datetime.now().astimezone().tzinfo


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data: dict[str, Any] = request.form.to_dict()
        method = data.pop('method')
        logger.debug(f'{request.referrer=} | {method=} | {data=}')
        match method:
            case 'add':
                # add local timezone if one isn't provided
                if not datetime.fromisoformat(data['date']).tzname:
                    data['date'] = datetime.fromisoformat(data['date']).replace(tzinfo=LOCAL_TZ)
                response = requests.post(EVENTS_API_URL, json=jsonable_encoder(data), timeout=TIMEOUT)
                if response.status_code != status.HTTP_201_CREATED:
                    log_flash_raise_error(response, logger)
            case 'delete':
                id = data.get('id')
                response = requests.delete(f'{EVENTS_API_URL}/{id}', timeout=TIMEOUT)
                if response.status_code != status.HTTP_204_NO_CONTENT:
                    log_flash_raise_error(response, logger)
            case 'attend':
                id = data.get('id')
                response = requests.post(f'{EVENTS_API_URL}/{id}/attend', timeout=TIMEOUT)
                if response.status_code != status.HTTP_200_OK:
                    log_flash_raise_error(response, logger)
            case _:
                return Response(f'Method {method} not allowed', status=status.HTTP_405_METHOD_NOT_ALLOWED)

    response = requests.get(EVENTS_API_URL, timeout=TIMEOUT)
    if response.status_code != status.HTTP_200_OK:
        log_flash_raise_error(response, logger)
    events = [schemas.Event(**event) for event in response.json()]
    return render_template('events/index.html', events=events)
