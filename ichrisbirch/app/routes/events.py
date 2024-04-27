import logging
from datetime import datetime
from typing import Any

import httpx
import pydantic
from fastapi import status
from flask import Blueprint, Response, flash, redirect, render_template, request, url_for

from ichrisbirch import schemas
from ichrisbirch.app.helpers import handle_if_not_response_code, url_builder
from ichrisbirch.config import get_settings

settings = get_settings()
blueprint = Blueprint('events', __name__, template_folder='templates/events', static_folder='static')

logger = logging.getLogger(__name__)

EVENTS_API_URL = f'{settings.api_url}/events/'

LOCAL_TZ = datetime.now().astimezone().tzinfo


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data: dict[str, Any] = request.form.to_dict()
        action = data.pop('action')
        logger.debug(f'{request.referrer=} {action=}')
        logger.debug(f'{data=}')

        if action == 'add':
            # add local timezone if one isn't provided
            if not datetime.fromisoformat(data['date']).tzname:
                data['date'] = datetime.fromisoformat(data['date']).replace(tzinfo=LOCAL_TZ)
            try:
                event = schemas.EventCreate(**data).model_dump_json()
            except pydantic.ValidationError as e:
                logger.exception(e)
                flash(str(e), 'error')
                return redirect(request.referrer or url_for('events.index'))
            response = httpx.post(EVENTS_API_URL, content=event)
            handle_if_not_response_code(201, response, logger)

        elif action == 'delete':
            url = url_builder(EVENTS_API_URL, str(data.get('id')))
            response = httpx.delete(url)
            handle_if_not_response_code(204, response, logger)

        elif action == 'attend':
            url = url_builder(EVENTS_API_URL, str(data.get('id')), 'attend')
            response = httpx.post(url)
            handle_if_not_response_code(200, response, logger)

        else:
            return Response(f'Method/Action {action} not allowed', status=status.HTTP_405_METHOD_NOT_ALLOWED)

    response = httpx.get(EVENTS_API_URL)
    handle_if_not_response_code(200, response, logger)
    events = [schemas.Event(**event) for event in response.json()]
    return render_template('events/index.html', events=events)
