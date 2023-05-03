import requests
from flask import Blueprint, redirect, render_template, request, url_for

from ichrisbirch.config import settings
from ichrisbirch.db.sqlalchemy import session
from ichrisbirch.models.box_packing import Box, Item

blueprint = Blueprint('box_packing', __name__, template_folder='templates/box_packing', static_folder='static')


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    """Box packing homepage"""
    last_box_id = request.args.get('last_box_id')
    box_id = last_box_id or request.form.get('selected_box_id')
    with session:
        boxes = session.query(Box).all()
        print('SELECTED BOX')
        print(session.get(Box, box_id))
        if selected_box := session.get(Box, box_id):
            print(selected_box)
            box_items = selected_box.items
            print(box_items)
        else:
            box_items = None

    return render_template(
        'box_packing/index.html',
        boxes=boxes,
        selected_box=selected_box,
        box_items=box_items,
    )


@blueprint.route('/all/', methods=['GET', 'POST'])
def all():
    """All packed boxes"""
    sort_1 = request.form.get('sort_1', '')
    sort_2 = request.form.get('sort_2', '')
    with session:
        boxes = session.query(Box)
        if sort_1:
            if not sort_2:
                boxes = boxes.order_by(getattr(Box, sort_1)).all()
            else:
                boxes = boxes.order_by(getattr(Box, sort_1), getattr(Box, sort_2)).all()
    return render_template('box_packing/all.html', boxes=boxes)


@blueprint.route('/search/', methods=['GET', 'POST'])
def search():
    """Search for a packed box"""
    search_text = request.form.get('search_text')
    results = session.query(Item).filter(Item.name.match(search_text)).all()
    return render_template(
        'box_packing/search.html',
        results=results,
    )


# TODO: [2023/02/10] - Make this crud instead of form
@blueprint.route('/form/', methods=['POST'])
def form():
    """CRUD operations for boxes"""
    api_url = settings.api_url
    data = request.form.to_dict()
    method = data.pop('method')
    match method:
        case ['add_box']:
            box = Box(**data)
            requests.post(f'{api_url}/boxes', data=box, timeout=settings.request_timeout)
        case ['delete_box']:
            box = Box(**data)
            requests.delete(f'{api_url}/boxes/{box.id}', timeout=settings.request_timeout)
        case ['add_item']:
            item = Item(**data)
            requests.post(f'{api_url}/boxes/items', data=box, timeout=settings.request_timeout)
        case ['delete_item']:
            item = Item(**data)
            requests.delete(f'{api_url}/boxes/items/{item.id}', timeout=settings.request_timeout)

    return redirect(url_for('box_packing.index'))
