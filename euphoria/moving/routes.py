from flask import Blueprint, redirect, render_template, request, url_for
from euphoria import db
from sqlalchemy import delete, select
from euphoria.moving.models import Box, Item

moving_bp = Blueprint(
    'moving_bp', __name__, template_folder='templates/moving', static_folder='static'
)


@moving_bp.route('/', methods=['GET', 'POST'])
def packing():
    last_box_id = request.args.get('last_box_id')
    box_sort_1 = request.form.get('box_sort_1')
    box_sort_2 = request.form.get('box_sort_2')
    box_id = last_box_id or request.form.get('selected_box_id', 1)
    # TODO: WTForms to get the Box.order_by
    boxes = db.session.execute(select(Box)).scalars().all()
    selected_box = (
        db.session.execute(select(Box).where(Box.id == box_id)).scalars().first()
    )
    box_items = (
        db.session.execute(select(Item).where(Item.box_id == box_id)).scalars().all()
    )
    return render_template(
        'packing.html',
        boxes=boxes,
        selected_box=selected_box,
        box_items=box_items,
    )


@moving_bp.route('/search/', methods=['GET', 'POST'])
def search():
    search_text = request.form.get('search_text')
    results = db.session.query(Item).filter(Item.name.match(search_text)).all()
    return render_template(
        'search.html',
        results=results,
    )


@moving_bp.route('/add_box/', methods=['POST'])
def add_box():
    db.session.add(Box(**request.form))
    db.session.commit()
    return redirect(url_for('moving_bp.packing'))


@moving_bp.route('/delete_box/', methods=['POST'])
def delete_box():
    db.session.execute(delete(Box).where(Box.id == request.form.get('id')))
    db.session.commit()
    return redirect(url_for('moving_bp.packing'))


@moving_bp.route('/add_item/', methods=['POST'])
def add_item():
    # TODO: There has to be a better way to get last box_id
    box_id = request.form.pop('box_id')
    db.session.add(Item(**request.form))
    db.session.commit()
    return redirect(url_for('moving_bp.packing', last_box_id=box_id))


@moving_bp.route('/delete_item/', methods=['POST'])
def delete_item():
    db.session.execute(delete(Item).where(Item.id == request.form.get('id')))
    db.session.commit()
    return redirect(url_for('moving_bp.packing'))
