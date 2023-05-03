import requests
from flask import Blueprint, render_template, request

from ichrisbirch.config import settings
from ichrisbirch.db.sqlalchemy import session
from ichrisbirch.models.event import Event

blueprint = Blueprint('events', __name__, template_folder='templates/events', static_folder='static')


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    """Events home"""
    with session:
        events = session.query(Event).order_by(Event.date).all()

    if request.method == 'POST':
        api_url = settings.api_url
        data = request.form.to_dict()
        method = data.pop('method')
        match method:
            case ['add']:
                event = Event(**data)
                requests.post(f'{api_url}/events', data=event, timeout=settings.request_timeout)
            case ['delete']:
                event_id = data.get('id')
                requests.delete(f'{api_url}/events/{event_id}', timeout=settings.request_timeout)

    return render_template('events/index.html', events=events)
