from flask import Blueprint, redirect, render_template, request, url_for
from euphoria import apt_db as db
from euphoria.apartments.helpers import convert_data_types_from_strings

apartments_bp = Blueprint(
    'apartments_bp',
    __name__,
    template_folder='templates/apartments',
    static_folder='static',
)


@apartments_bp.route('/', methods=['GET', 'POST'])
@apartments_bp.route('/<int:aptid>/', methods=['GET', 'POST'])
def compare(aptid=1):
    feature_type_map = db.get_feature_types()
    if request.method == 'POST':
        aptid = request.form.get('id')
        features = request.form
        features = convert_data_types_from_strings(features, feature_type_map)
        db.update_features(features)
    current_apt = db.get_apartment(aptid)
    current_apt.pop('id')
    name = current_apt.pop('name')
    address = current_apt.pop('address')
    url = current_apt.pop('url')
    notes = current_apt.pop('notes')
    apartments = db.get_all_apartments()
    return render_template(
        'compare.html',
        apartments=apartments,
        aptid=aptid,
        current_apt=current_apt,
        name=name,
        address=address,
        url=url,
        notes=notes,
        feature_type_map=feature_type_map,
    )


@apartments_bp.route('/add_feature/', methods=['POST'])
def add_feature():
    name = request.form.get('name')
    name = name.replace(' ', '_').lower()
    type = request.form.get('type')
    aptid = request.form.get('aptid')
    db.add_feature(name, type)
    return redirect(url_for('apartments_bp.compare', aptid=aptid))


@apartments_bp.route('/delete_apartment/', methods=['POST'])
def delete_apartment():
    id = request.form.get('id')
    print(request.form)
    db.delete_apartment(id)
    return redirect(url_for('apartments_bp.manage'))


@apartments_bp.route('/update_apartment/', methods=['POST'])
def update_apartment():
    id = request.form.get('id')
    update_info = request.form
    print(update_info)
    db.update_apartment(update_info)
    return redirect(url_for('apartments_bp.manage', aptid=id))


@apartments_bp.route('/manage/', methods=['GET', 'POST'])
@apartments_bp.route('/manage/<int:aptid>/', methods=['GET', 'POST'])
def manage(aptid=1):
    apartments = db.get_all_apartments()
    apt = db.get_apartment(aptid)
    id = apt.get('id')
    name = apt.get('name')
    address = apt.get('address')
    url = apt.get('url')
    return render_template(
        'manage.html',
        apartments=apartments,
        aptid=aptid,
        id=id,
        name=name,
        address=address,
        url=url,
    )
