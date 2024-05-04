import logging

from flask import Blueprint
from flask import render_template
from flask_login import current_user
from flask_login import fresh_login_required
from flask_login import login_required

from ichrisbirch import schemas
from ichrisbirch.app.query_api import QueryAPI

blueprint = Blueprint('users', __name__, template_folder='templates/users', static_folder='static')
logger = logging.getLogger(__name__)

users_api = QueryAPI(base_url='users', api_key='', logger=logger, response_model=schemas.User)


@blueprint.route('/profile/', methods=['GET'])
@login_required
def profile():
    return render_template('users/profile.html', user=current_user)


@blueprint.route('/update/', methods=['GET', 'POST'])
@fresh_login_required
def update():
    return render_template('users/update.html', user=current_user)
