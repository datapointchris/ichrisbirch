import logging

from flask import Blueprint
from flask import render_template
from flask_login import login_required

from ichrisbirch.config import settings

logger = logging.getLogger('app.chat')

blueprint = Blueprint('chat', __name__, template_folder='templates/chat', static_folder='static')


@blueprint.before_request
@login_required
def enforce_login():
    pass


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    return render_template('chat/index.html', chat_url=settings.chat_url)
