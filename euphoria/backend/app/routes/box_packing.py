from flask import Blueprint, redirect, render_template, request, url_for, current_app
from ..models.box_packing import Box, Item
from ..db.sqlalchemy import session
import requests

blueprint = Blueprint(
    'box_packing', __name__, template_folder='templates/box_packing', static_folder='static'
)




@blueprint.route('/', methods=['GET', 'POST'])
def index():
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
    search_text = request.form.get('search_text')
    results = session.query(Item).filter(Item.name.match(search_text)).all()
    return render_template(
        'box_packing/search.html',
        results=results,
    )


@blueprint.route('/form/', methods=['POST'])
def form():
    api_url = current_app.config.get('API_URL')
    data = request.form.to_dict()
    method = data.pop('method')
    match method:
        case ['add_box']:
            box = Box(**data)
            requests.post(f'{api_url}/boxes', data=box)
        case ['delete_box']:
            box = Box(**data)
            requests.delete(f'{api_url}/boxes/{box.id}')
        case ['add_item']:
            item = Item(**data)
            requests.post(f'{api_url}/boxes/items', data=box)
        case ['delete_item']:
            item = Item(**data)
            requests.delete(f'{api_url}/boxes/items/{item.id}')

    return redirect(url_for('box_packing.index'))
