from flask import Blueprint, redirect, render_template, request, url_for
from euphoria import db
from euphoria.apartments.models import Apartment, Feature
from sqlalchemy import select, delete, update

apartments_bp = Blueprint(
    'apartments_bp',
    __name__,
    template_folder='templates/apartments',
    static_folder='static',
)


@apartments_bp.route('/', methods=['GET', 'POST'])
@apartments_bp.route('/<int:id>/', methods=['GET', 'POST'])
def apartments(id=1):
    apartment = (
        db.session.execute(select(Apartment).where(Apartment.id == id)).scalars().first()
    )
    features = (
        db.session.execute(select(Feature).where(Feature.apartment_id == id))
        .scalars()
        .all()
    )
    print(features)
    apartments = db.session.execute(select(Apartment)).scalars().all()
    return render_template(
        'apartments.html', apartment=apartment, apartments=apartments, features=features
    )


@apartments_bp.route('/manage/')
@apartments_bp.route('/manage/<int:id>/')
def manage(id=1):
    apartment = (
        db.session.execute(select(Apartment).where(Apartment.id == id)).scalars().first()
    )
    apartments = db.session.execute(select(Apartment)).scalars().all()
    return render_template(
        'manage.html',
        apartment=apartment,
        apartments=apartments,
    )


# not implemented
@apartments_bp.route('/add_apartment/', methods=['POST'])
def add_apartment():
    db.session.add(Apartment(**request.form))
    db.session.commit()
    return redirect(url_for('apartments_bp.apartments'))


@apartments_bp.route('/update_apartment/', methods=['POST'])
def update_apartment():
    apartment = request.form
    db.session.execute(
        update(Apartment).where(Apartment.id == apartment.get('id')).values(**apartment)
    )
    db.session.commit()
    return redirect(url_for('apartments_bp.apartments', aptid=apartment.get('id')))


@apartments_bp.route('/delete_apartment/', methods=['POST'])
def delete_apartment():
    db.session.execute(delete(Apartment).where(Apartment.id == request.form.get('id')))
    db.session.commit()
    return redirect(url_for('apartments_bp.apartments'))


@apartments_bp.route('/add_feature/', methods=['POST'])
def add_feature():
    db.session.add(Feature(**request.form))
    db.session.commit()
    return redirect(url_for('apartments_bp.apartments', aptid=request.form.get('apt_id')))


# not implemented right now
@apartments_bp.route('/delete_feature/', methods=['POST'])
def delete_feature():
    db.session.execute(delete(Feature).where(Feature.id == request.form.get('id')))
    db.session.commit()
    return redirect(url_for('apartments_bp.manage'))
