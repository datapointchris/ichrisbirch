import logging
from typing import Any

import httpx
import pydantic
from fastapi import status
from flask import Blueprint
from flask import Response
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from ichrisbirch import schemas
from ichrisbirch.app import utils
from ichrisbirch.config import get_settings
from ichrisbirch.models.box import BoxSize

settings = get_settings()
logger = logging.getLogger('app.box_packing')
blueprint = Blueprint('box_packing', __name__, template_folder='templates/box_packing', static_folder='static')


BOX_PACKING_API_URL = f'{settings.api_url}/box_packing/'
BOXES_API_URL = utils.url_builder(BOX_PACKING_API_URL, 'boxes')
ITEMS_API_URL = utils.url_builder(BOX_PACKING_API_URL, 'items')
BOX_SIZES = [s.value for s in BoxSize]


@blueprint.route('/', methods=['GET'])
def index():
    response = httpx.get(utils.url_builder(BOXES_API_URL))
    utils.handle_if_not_response_code(200, response, logger)
    boxes = [schemas.Box(**box) for box in response.json()]
    return render_template('box_packing/index.html', selected_box=None, boxes=boxes, box_sizes=BOX_SIZES)


@blueprint.route('/<box_id>/', methods=['GET'])
def box(box_id):
    response = httpx.get(utils.url_builder(BOXES_API_URL))
    utils.handle_if_not_response_code(200, response, logger)
    boxes = [schemas.Box(**box) for box in response.json()]
    logger.debug(f'{box_id=}')
    selected_box = next((box for box in boxes if str(box.id) == box_id), None)
    if not selected_box:
        flash(f'Box {box_id} not found', 'error')
        logger.warning(f'box {box_id} not found')
        return redirect(url_for('box_packing.index'))
    logger.debug(f'{selected_box=}')
    return render_template('box_packing/index.html', selected_box=selected_box, boxes=boxes, box_sizes=BOX_SIZES)


@blueprint.route('/all/', methods=['GET', 'POST'])
def all():
    sort_1 = request.form.get('sort_1')
    sort_2 = request.form.get('sort_2')
    logger.debug(f'{sort_1=} {sort_2=}')

    params = {'sort_1': sort_1, 'sort_2': sort_2}
    response = httpx.get(BOXES_API_URL, params=params)
    utils.handle_if_not_response_code(200, response, logger)
    boxes = [schemas.Box(**box) for box in response.json()]
    logger.debug(f'{boxes=}')
    # TODO: check if sort_1 will always be present
    if sort_1:
        if sort_2:
            boxes = sorted(boxes, key=lambda box: (getattr(box, sort_1), getattr(box, sort_2)))
        else:
            boxes = sorted(boxes, key=lambda box: getattr(box, sort_1))
    return render_template('box_packing/all.html', boxes=boxes, sort_1=sort_1, sort_2=sort_2, box_sizes=BOX_SIZES)


@blueprint.route('/search/', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        data: dict[str, Any] = request.form.to_dict()
        search_text = data.get('search_text')
        logger.debug(f'{request.referrer=} | {search_text=}')
        if not search_text:
            flash('No search terms provided', 'warning')
            return render_template('box_packing/search.html', results=[])
        search_url = utils.url_builder(BOX_PACKING_API_URL, 'search')
        response = httpx.get(search_url, params={'q': search_text})
        logger.debug(f'{response.json()=}')
        utils.handle_if_not_response_code(200, response, logger)
        results = [schemas.BoxItem(**item) for item in response.json()]
    else:
        results = []
    return render_template('box_packing/search.html', results=results)


@blueprint.route('/crud/', methods=['POST'])
def crud():
    data: dict[str, Any] = request.form.to_dict()
    action = data.pop('action')
    logger.debug(f'{request.referrer=} {action=}')
    logger.debug(f'{data=}')

    if action == 'add_box':
        try:
            essential = bool(data.pop('essential', 0))
            warm = bool(data.pop('warm', 0))
            liquid = bool(data.pop('liquid', 0))
            box = schemas.BoxCreate(**data, essential=essential, warm=warm, liquid=liquid)
        except pydantic.ValidationError as e:
            logger.exception(e)
            flash(str(e), 'error')
            return redirect(request.referrer or url_for('box_packing.index'))
        response = httpx.post(BOXES_API_URL, content=box.model_dump_json())
        utils.handle_if_not_response_code(201, response, logger)
        flash(f'Box {box.name} added', 'success')
        try:
            new_box = schemas.Box(**response.json())
        except pydantic.ValidationError as e:
            logger.exception(e)
            flash(str(e), 'error')
            return redirect(request.referrer or url_for('box_packing.index'))
        return redirect(request.referrer or url_for('box_packing.box', box_id=new_box.id))

    if action == 'delete_box':
        url = utils.url_builder(BOXES_API_URL, data.get('id'))
        response = httpx.delete(url)
        utils.handle_if_not_response_code(204, response, logger)
        flash(f'Box {data.get("name")} deleted', 'success')
        return redirect(request.referrer or url_for('box_packing.index'))

    if action == 'add_item':
        try:
            essential = bool(data.pop('essential', 0))
            warm = bool(data.pop('warm', 0))
            liquid = bool(data.pop('liquid', 0))
            item = schemas.BoxItemCreate(**data, essential=essential, warm=warm, liquid=liquid)
        except pydantic.ValidationError as e:
            logger.error(e)
            flash(str(e), 'error')
            return redirect(request.referrer or url_for('box_packing.index'))
        response = httpx.post(ITEMS_API_URL, content=item.model_dump_json())
        utils.handle_if_not_response_code(201, response, logger)
        flash(f'Item {item.name} added to box {item.box_id}', 'success')
        return redirect(url_for('box_packing.box', box_id=item.box_id))

    if action == 'delete_item':
        item_id = data.get('id')
        box_id = data.get('box_id')
        url = utils.url_builder(ITEMS_API_URL, item_id)
        response = httpx.delete(url)
        utils.handle_if_not_response_code(204, response, logger)
        flash(f'Item {item_id} deleted from box {box_id}', 'success')
        return redirect(request.referrer or url_for('box_packing.box', box_id=box_id))

    return Response(f'Method/Action {action} not accepted', status=status.HTTP_405_METHOD_NOT_ALLOWED)
