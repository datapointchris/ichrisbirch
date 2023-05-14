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
    try:
        response = requests.get(COUNTDOWNS_URL, timeout=TIMEOUT).json()
    except Exception as e:
        error_message = f'{__file__}: Error retrieving countdowns from API: {e}'
        logger.error(error_message)
        flash(error_message, 'error')
        response = None
    countdowns = [schemas.Countdown(**countdown) for countdown in response] if response else []

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
            try:
                countdown = schemas.CountdownCreate(**data).json()
                requests.post(COUNTDOWNS_URL, data=countdown, timeout=TIMEOUT)
                flash('Countdown created', 'success')
            except Exception as e:
                error_message = f'Error creating countdown: {e}'
                logger.error(error_message)
                flash(error_message, 'error')
            return redirect(url_for('countdowns.index'))
        case 'delete':
            try:
                countdown_id = data.get('id')
                requests.delete(f'{COUNTDOWNS_URL}/{countdown_id}', timeout=TIMEOUT)
                flash('Countdown deleted', 'success')
            except Exception as e:
                error_message = f'Error deleting countdown: {e}'
                logger.error(error_message)
                flash(error_message, 'error')
            return redirect(url_for('countdowns.index'))
    return abort(405, description=f"Method {method} not accepted")
