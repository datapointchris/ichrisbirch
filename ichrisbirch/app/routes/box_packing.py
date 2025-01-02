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
from flask_login import login_required

from ichrisbirch import schemas
from ichrisbirch.app.query_api import QueryAPI
from ichrisbirch.config import get_settings
from ichrisbirch.models.box import BoxSize

BOX_SIZES = [s.value for s in BoxSize]
settings = get_settings()
logger = logging.getLogger('app.box_packing')
blueprint = Blueprint('box_packing', __name__, template_folder='templates/box_packing', static_folder='static')


@blueprint.before_request
@login_required
def enforce_login():
    pass


@blueprint.route('/', defaults={'box_id': None}, methods=['GET'])
@blueprint.route('/<box_id>/', methods=['GET'])
def index(box_id):
    boxes_api = QueryAPI(base_url='box-packing/boxes', logger=logger, response_model=schemas.Box)
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
    boxes_api = QueryAPI(base_url='box-packing/boxes', logger=logger, response_model=schemas.Box)
    sort_1 = request.form.get('sort_1')
    sort_2 = request.form.get('sort_2')
    logger.debug(f'{sort_1=} {sort_2=}')

    boxes = boxes_api.get_many()
    if sort_1:
        if sort_2:
            boxes = sorted(boxes, key=lambda box: (getattr(box, sort_1), getattr(box, sort_2)))
        else:
            boxes = sorted(boxes, key=lambda box: getattr(box, sort_1))
    return render_template('box_packing/all.html', boxes=boxes, sort_1=sort_1, sort_2=sort_2, box_sizes=BOX_SIZES)


@blueprint.route('/orphans/', methods=['GET', 'POST'])
def orphans():
    boxes_api = QueryAPI(base_url='box-packing/boxes', logger=logger, response_model=schemas.Box)
    boxitem_orphans_api = QueryAPI(base_url='box-packing/items/orphans', logger=logger, response_model=schemas.BoxItem)
    sort = request.form.get('sort', 'name')
    logger.debug(f'{sort=}')

    orphans = boxitem_orphans_api.get_many()
    orphans = sorted(orphans, key=lambda boxitem: getattr(boxitem, sort))
    boxes = boxes_api.get_many()
    return render_template('box_packing/orphans.html', boxes=boxes, orphans=orphans, sort=sort)


@blueprint.route('/search/', methods=['GET', 'POST'])
def search():
    """Search for box items."""
    results: list[tuple[schemas.Box, schemas.BoxItem]] = []
    if request.method == 'POST':
        box_search_api = QueryAPI(
            base_url='box-packing/search', logger=logger, response_model=(schemas.Box, schemas.BoxItem)
        )
        data: dict[str, Any] = request.form.to_dict()
        if search_text := data.get('search_text'):
            logger.debug(f'{request.referrer=} | {search_text=}')
            if rows := box_search_api.get_generic(params={'q': search_text}):
                results = [(schemas.Box(**row[0]), schemas.BoxItem(**row[1])) for row in rows]
        else:
            flash('No search terms provided', 'warning')
    return render_template('box_packing/search.html', results=results)


@blueprint.route('/crud/', methods=['POST'])
def crud():
    boxes_api = QueryAPI(base_url='box-packing/boxes', logger=logger, response_model=schemas.Box)
    boxitems_api = QueryAPI(base_url='box-packing/items', logger=logger, response_model=schemas.BoxItem)
    data: dict = request.form.to_dict()
    action = data.pop('action')
    logger.debug(f'{request.referrer=} {action=}')

    match action:
        case 'add_box':
            essential = bool(data.pop('essential', 0))
            warm = bool(data.pop('warm', 0))
            liquid = bool(data.pop('liquid', 0))
            box = data | dict(essential=essential, warm=warm, liquid=liquid)
            if new_box := boxes_api.post(json=box):
                flash(f'Box {new_box.id}: {new_box.name} created', 'success')
                box_id = new_box.id

        case 'delete_box':
            box_id = data.get('box_id')
            box_name = data.get('box_name')
            if boxes_api.delete(box_id):
                flash(f'Box {box_name} deleted', 'success')
            box_id = None

        case 'add_item':
            box_id = data.get('box_id')
            box_name = data.get('box_name')
            essential = bool(data.pop('essential', 0))
            warm = bool(data.pop('warm', 0))
            liquid = bool(data.pop('liquid', 0))
            box_item = data | dict(essential=essential, warm=warm, liquid=liquid)
            if item := boxitems_api.post(json=box_item):
                flash(f'{item.name} added to Box {item.box_id}: {box_name}', 'success')

        case 'delete_item':
            item_id = data.get('item_id')
            item_name = data.get('item_name')
            box_id = data.get('box_id')
            box_name = data.get('box_name')
            if boxitems_api.delete(item_id):
                flash(f'{item_name} deleted from Box {box_id}: {box_name}', 'success')

        case 'orphan_item':
            logger.warning('Orphan item not implemented')
            item_id = data.get('item_id')
            item_name = data.get('item_name')
            box_id = data.get('box_id')
            box_name = data.get('box_name')
            logger.warning(f'{item_id=} {item_name=} {box_id=} {box_name=}')
            if boxitems_api.patch(item_id, json={'id': item_id, 'box_id': None}):
                flash(f'{item_name} orphaned from Box {box_id}: {box_name}', 'success')

        case 'add_orphan_to_box':
            box_id = data.get('box_id')
            box_name = data.get('box_name')
            item_id = data.get('item_id')
            item_name = data.get('item_name')
            if boxitems_api.patch(item_id, json={'id': item_id, 'box_id': box_id}):
                flash(f'{item_name} added to Box {box_id}: {box_name}', 'success')

        case 'delete_orphan':
            item_id = data.get('item_id')
            item_name = data.get('item_name')
            if boxitems_api.delete(item_id):
                flash(f'Orphan {item_name} deleted', 'success')
            return redirect(url_for('box_packing.orphans'))

        case _:
            return Response(f'Method/Action {action} not accepted', status=status.HTTP_405_METHOD_NOT_ALLOWED)

    return redirect(url_for('box_packing.index', box_id=box_id) if box_id else url_for('box_packing.index'))
