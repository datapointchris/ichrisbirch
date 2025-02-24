import logging

from fastapi import status
from flask import Blueprint
from flask import Response
from flask import render_template
from flask import request
from flask_login import login_required

from ichrisbirch import schemas
from ichrisbirch.app.query_api import QueryAPI

logger = logging.getLogger('app.money_wasted')
blueprint = Blueprint('money_wasted', __name__, template_folder='templates/money_wasted', static_folder='static')


@blueprint.before_request
@login_required
def enforce_login():
    pass


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    money_wasted_api = QueryAPI(base_url='money-wasted', response_model=schemas.MoneyWasted)
    if request.method == 'POST':
        data = request.form.to_dict()
        action = data.pop('action')

        match action:
            case 'add':
                money_wasted_api.post(json=data)
            case 'delete':
                money_wasted_api.delete(data.get('id'))
            case _:
                return Response(f'Method/Action {action} not allowed', status=status.HTTP_405_METHOD_NOT_ALLOWED)

    money_wasted = money_wasted_api.get_many()
    total_money_wasted = sum([item.amount for item in money_wasted])
    return render_template('money_wasted/index.html', money_wasted=money_wasted, total_money_wasted=total_money_wasted)
