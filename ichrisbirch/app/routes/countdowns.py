import requests
from flask import Blueprint, render_template, request

from ichrisbirch.config import settings
from ichrisbirch.db.sqlalchemy import session
from ichrisbirch.models.countdowns import Countdown

blueprint = Blueprint('countdowns', __name__, template_folder='templates/countdowns', static_folder='static')


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    """Countdowns home"""
    with session:
        countdowns = session.query(Countdown).order_by(Countdown.date).all()

    if request.method == 'POST':
        api_url = settings.API_URL
        data = request.form.to_dict()
        method = data.pop('method')
        match method:
            case ['add']:
                countdown = Countdown(**data)
                requests.post(f'{api_url}/countdowns', data=countdown, timeout=settings.REQUEST_TIMEOUT)
            case ['delete']:
                countdown_id = data.get('id')
                requests.delete(f'{api_url}/countdowns/{countdown_id}', timeout=settings.REQUEST_TIMEOUT)

    return render_template('countdowns/index.html', countdowns=countdowns)
