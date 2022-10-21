from flask import Blueprint, render_template, request, current_app
from ...common.models.events import Event
from ...common.db.sqlalchemy import session
import requests

blueprint = Blueprint(
    'events', __name__, template_folder='templates/events', static_folder='static'
)


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    with session:
        events = session.query(Event).order_by(Event.date).all()

    if request.method == 'POST':
        api_url = SETTINGS.API_URL
        data = request.form.to_dict()
        method = data.pop('method')
        match method:
            case ['add']:
                event = Event(**data)
                requests.post(f'{api_url}/events', data=event)
            case ['delete']:
                event_id = data.get('id')
                requests.delete(f'{api_url}/events/{event_id}')

    return render_template('events/index.html', events=events)
