import logging
from typing import Any

import requests
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ichrisbirch import schemas
from ichrisbirch.config import get_settings

settings = get_settings()
blueprint = Blueprint('countdowns', __name__, template_folder='templates/countdowns', static_folder='static')

logger = logging.getLogger(__name__)

COUNTDOWNS_URL = f'{settings.api_url}/countdowns'
TIMEOUT = settings.request_timeout


@blueprint.route('/', methods=['GET'])
def index():
    """Countdowns home endpoint"""
    response = requests.get(COUNTDOWNS_URL, timeout=TIMEOUT)
    if response.status_code == 200:
        countdowns = [schemas.Countdown(**countdown) for countdown in response.json()]
    else:
        error_message = f'{response.url} : {response.status_code} {response.reason}'
        logger.error(error_message)
        flash(error_message, 'error')
        countdowns = []

    return render_template('countdowns/index.html', countdowns=countdowns)


@blueprint.route('/crud/', methods=['POST'])
def crud():
    """CRUD endpoint for countdowns"""
    data: dict[str, Any] = request.form.to_dict()
    method = data.pop('method')
    logger.debug(f'{request.referrer=}')
    logger.debug(f'{method=}')
    logger.debug(f'{data}')
    match method:
        case 'add':
            countdown = schemas.CountdownCreate(**data).json()
            response = requests.post(COUNTDOWNS_URL, data=countdown, timeout=TIMEOUT)
            logger.debug(response.text)
            if response.status_code == 201:
                flash(f'Countdown added: {data.get("name")}', 'success')
            else:
                error_message = f'{response.url} : {response.status_code} {response.reason}'
                logger.error(error_message)
                flash(error_message, 'error')
            return redirect(url_for('countdowns.index'))

        case 'delete':
            id = data.get('id')
            response = requests.delete(f'{COUNTDOWNS_URL}/{id}', timeout=TIMEOUT)
            logger.debug(response.text)
            if response.status_code == 204:
                flash(f'Countdown deleted: {data.get("name")}', 'success')
            else:
                error_message = f'{response.url} : {response.status_code} {response.reason}'
                logger.error(error_message)
                flash(error_message, 'error')
            return redirect(url_for('countdowns.index'))

    return abort(405, description=f"Method {method} not accepted")
