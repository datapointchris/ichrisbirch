import logging
from typing import Any

import requests
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ichrisbirch import schemas
from ichrisbirch.app.routes.util import validate_response
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
    if validate_response(response):
        countdowns = [schemas.Countdown(**countdown) for countdown in response.json()]
    else:
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
            if validate_response(response):
                flash(f'Countdown added: {data.get("name")}', 'success')
            logger.debug(response.text)
            return redirect(url_for('countdowns.index'))
        case 'delete':
            id = data.get('id')
            response = requests.delete(f'{COUNTDOWNS_URL}/{id}', timeout=TIMEOUT)
            if validate_response(response):
                flash(f'Countdown deleted: {data.get("name")}', 'success')
            logger.debug(response.text)
            return redirect(url_for('countdowns.index'))
    return abort(405, description=f"Method {method} not accepted")
