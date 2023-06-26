import logging
from typing import Any

import requests
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ichrisbirch import schemas
from ichrisbirch.config import get_settings

settings = get_settings()
blueprint = Blueprint('events', __name__, template_folder='templates/events', static_folder='static')

logger = logging.getLogger(__name__)

EVENTS_URL = f'{settings.api_url}/events'
TIMEOUT = settings.request_timeout


@blueprint.route('/', methods=['GET'])
def index():
    response = requests.get(EVENTS_URL, timeout=TIMEOUT)
    if response.status_code == 200:
        events = [schemas.Event(**event) for event in response.json()]
    else:
        error_message = f'{response.url} : {response.status_code} {response.reason}'
        logger.error(error_message)
        flash(error_message, 'error')
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
            event = schemas.EventCreate(**data).json()
            response = requests.post(EVENTS_URL, data=event, timeout=TIMEOUT)
            logger.debug(response.text)
            if response.status_code == 201:
                flash(f'Event added: {data.get("name")}', 'success')
            else:
                error_message = f'{response.url} : {response.status_code} {response.reason}'
                logger.error(error_message)
                logger.error(response.text)
                flash(error_message, 'error')
                flash(response.text, 'error')
            return redirect(url_for('events.index'))

        case 'delete':
            id = data.get('id')
            response = requests.delete(f'{EVENTS_URL}/{id}', timeout=TIMEOUT)
            logger.debug(response.text)
            if response.status_code == 204:
                flash(f'Event deleted: {data.get("name")}', 'success')
            else:
                error_message = f'{response.url} : {response.status_code} {response.reason}'
                logger.error(error_message)
                flash(error_message, 'error')
            return redirect(url_for('events.index'))

    return abort(405, description=f"Method {method} not accepted")
