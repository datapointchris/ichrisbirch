import logging

from flask import Blueprint
from flask import redirect
from flask_login import login_required

from ichrisbirch.config import get_settings

logger = logging.getLogger('app.chat')
settings = get_settings()
blueprint = Blueprint('chat', __name__, template_folder='templates/chat', static_folder='static')


@blueprint.before_request
@login_required
def enforce_login():
    pass


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    return redirect(settings.chat_url)
