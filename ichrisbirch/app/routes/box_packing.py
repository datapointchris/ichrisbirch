import logging
from typing import Any

from fastapi import status
from flask import Blueprint
from flask import Response
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from ichrisbirch import schemas
from ichrisbirch.app.query_api import QueryAPI
from ichrisbirch.config import get_settings
from ichrisbirch.models.box import BoxSize

settings = get_settings()
logger = logging.getLogger('app.box_packing')
blueprint = Blueprint('box_packing', __name__, template_folder='templates/box_packing', static_folder='static')
BOX_SIZES = [s.value for s in BoxSize]


@blueprint.route('/', defaults={'box_id': None}, methods=['GET'])
@blueprint.route('/<box_id>/', methods=['GET'])
def index(box_id):
    boxes_api = QueryAPI(base_url='box_packing/boxes', logger=logger, response_model=schemas.Box)
    boxes = boxes_api.get_many()
    selected_box = None
    if box_id:
        logger.debug(f'{box_id=}')
        if selected_box := next((box for box in boxes if str(box.id) == box_id), None):
            logger.debug(f'{selected_box.name=}')
        else:
            msg = f'Box {box_id} not found'
            flash(msg, 'error')
            logger.warning(msg.lower())
    return render_template('box_packing/index.html', selected_box=selected_box, boxes=boxes, box_sizes=BOX_SIZES)


@blueprint.route('/all/', methods=['GET', 'POST'])
def all():
    boxes_api = QueryAPI(base_url='box_packing/boxes', logger=logger, response_model=schemas.Box)
    sort_1 = request.form.get('sort_1')
    sort_2 = request.form.get('sort_2')
    logger.debug(f'{sort_1=} {sort_2=}')

    params = {'sort_1': sort_1, 'sort_2': sort_2}
    boxes = boxes_api.get_many(params=params)
    if sort_1:
        if sort_2:
            boxes = sorted(boxes, key=lambda box: (getattr(box, sort_1), getattr(box, sort_2)))
        else:
            boxes = sorted(boxes, key=lambda box: getattr(box, sort_1))
    return render_template('box_packing/all.html', boxes=boxes, sort_1=sort_1, sort_2=sort_2, box_sizes=BOX_SIZES)


@blueprint.route('/search/', methods=['GET', 'POST'])
def search():
    results = []
    if request.method == 'POST':
        box_search_api = QueryAPI(base_url='box_packing/search', logger=logger, response_model=schemas.BoxItem)
        data: dict[str, Any] = request.form.to_dict()
        if search_text := data.get('search_text'):
            logger.debug(f'{request.referrer=} | {search_text=}')
            results = box_search_api.get_many(params={'q': search_text})
        else:
            flash('No search terms provided', 'warning')
    return render_template('box_packing/search.html', results=results)


@blueprint.route('/crud/', methods=['POST'])
def crud():
    boxes_api = QueryAPI(base_url='box_packing/boxes', logger=logger, response_model=schemas.Box)
    boxitems_api = QueryAPI(base_url='box_packing/items', logger=logger, response_model=schemas.BoxItem)
    data: dict = request.form.to_dict()
    action = data.pop('action')
    logger.debug(f'{request.referrer=} {action=}')

    match action:
        case 'add_box':
            essential = bool(data.pop('essential', 0))
            warm = bool(data.pop('warm', 0))
            liquid = bool(data.pop('liquid', 0))
            box = data | dict(essential=essential, warm=warm, liquid=liquid)
            new_box = boxes_api.post(json=box)
            box_id = new_box.id

        case 'delete_box':
            box_name = data.get('name')
            boxes_api.delete(data.get('id'))
            flash(f'Box {box_name} deleted', 'success')
            box_id = None

        case 'add_item':
            essential = bool(data.pop('essential', 0))
            warm = bool(data.pop('warm', 0))
            liquid = bool(data.pop('liquid', 0))
            box_item = data | dict(essential=essential, warm=warm, liquid=liquid)
            item = boxitems_api.post(json=box_item)
            flash(f'Item {item.name} added to box {item.box_id}', 'success')
            box_id = item.box_id

        case 'delete_item':
            item_id = data.get('id')
            box_id = data.get('box_id')
            boxitems_api.delete(item_id)
            flash(f'Item {item_id} deleted from box {box_id}', 'success')

        case _:
            return Response(f'Method/Action {action} not accepted', status=status.HTTP_405_METHOD_NOT_ALLOWED)

    return redirect(url_for('box_packing.index', box_id=box_id) if box_id else url_for('box_packing.index'))
