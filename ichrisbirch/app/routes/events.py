import logging
from typing import Any

import pydantic
import requests
from fastapi import status
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ichrisbirch import schemas
from ichrisbirch.config import get_settings

settings = get_settings()
blueprint = Blueprint('events', __name__, template_folder='templates/events', static_folder='static')

logger = logging.getLogger(__name__)

EVENTS_API_URL = f'{settings.api_url}/events'
TIMEOUT = settings.request_timeout


@blueprint.route('/', methods=['GET'])
def index():
    response = requests.get(EVENTS_API_URL, timeout=TIMEOUT)
    if response.status_code == status.HTTP_200_OK:
        events = [schemas.Event(**event) for event in response.json()]
    else:
        error_message = f'{response.url} : {response.status_code} {response.reason}'
        logger.error(error_message)
        logger.error(response.text)
        flash(error_message, 'error')
        flash(response.text, 'error')
        events = []
    return render_template('events/index.html', events=events)


@blueprint.route('/crud/', methods=['POST'])
def crud():
    data: dict[str, Any] = request.form.to_dict()
    method = data.pop('method')
    logger.debug(f'{request.referrer=}')
    logger.debug(f'{method=}')
    logger.debug(f'{data}')
    match method:
        case 'add':
            try:
                event = schemas.EventCreate(**data).json()
            except pydantic.ValidationError as e:
                logger.exception(e)
                flash(str(e), 'error')
                return redirect(url_for('events.index'))
            logger.debug(f'Event: {event} validated successfully')
            response = requests.post(EVENTS_API_URL, data=event, timeout=TIMEOUT)
            logger.debug(f'{response=}')
            if response.status_code != status.HTTP_201_CREATED:
                error_message = f'{response.url} : {response.status_code} {response.reason}'
                logger.error(error_message)
                logger.error(response.text)
                flash(error_message, 'error')
                flash(response.text, 'error')
            return redirect(url_for('events.index'))

        case 'delete':
            id = data.get('id')
            logger.debug(f'{id=}')
            response = requests.delete(f'{EVENTS_API_URL}/{id}', timeout=TIMEOUT)
            logger.debug(f'{response=}')
            if response.status_code != status.HTTP_204_NO_CONTENT:
                error_message = f'{response.url} : {response.status_code} {response.reason}'
                logger.error(error_message)
                logger.error(response.text)
                flash(error_message, 'error')
                flash(response.text, 'error')
            return redirect(url_for('events.index'))

    return abort(status.HTTP_405_METHOD_NOT_ALLOWED, description=f"Method {method} not accepted")
