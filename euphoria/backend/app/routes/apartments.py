from flask import Blueprint, redirect, render_template, request, url_for, current_app
from ...common.models.apartments import Apartment, Feature
import requests

blueprint = Blueprint(
    'apartments',
    __name__,
    template_folder='templates/apartments',
    static_folder='static',
)


@blueprint.route('/')
def index():
    apartments = [apt for apt in Apartment.scan()]
    return render_template(
        'apartments.html',
        apartments=apartments,
        apartment=None,
        features=None,
        message='No apartment selected',
    )


@blueprint.route('/<string:name>/')
def apartment(name):
    apartments = [apt for apt in Apartment.scan()]
    if apartment := next((apt for apt in apartments if apt.name == name), None):
        features = [Feature(**f) for f in apartment.features]
        return render_template(
            'apartments.html',
            apartments=apartments,
            apartment=apartment,
            features=features,
            message=None,
        )
    else:
        return render_template(
            'apartments.html',
            apartments=apartments,
            apartment=None,
            features=None,
            message=f'{name} apartment does not exist',
        )


# transparently redirect to main page
@blueprint.route('/edit/')
def noedit():
    apartments = [apt for apt in Apartment.scan()]
    return render_template(
        'apartments.html',
        apartments=apartments,
        apartment=None,
        features=None,
        message='No apartment selected',
    )


@blueprint.route('/edit/<string:name>/')
def edit(name):
    apartments = [apt for apt in Apartment.scan()]
    if apartment := next((apt for apt in apartments if apt.name == name), None):
        features = [Feature(**f) for f in apartment.features]
        return render_template(
            'edit.html',
            apartments=apartments,
            apartment=apartment,
            features=features,
            message=None,
        )
    else:
        return render_template(
            'apartments.html',
            apartments=apartments,
            apartment=None,
            features=None,
            message=f'{name} apartment does not exist',
        )


@blueprint.route('/form/', methods=['POST'])
def crud():
    api_url = current_app.config.get('API_URL')
    data = request.form.to_dict()
    method = data.pop('method')
    apt = Apartment(**data)
    if method == 'add':
        requests.post(f'{api_url}/tasks', data=apt)
    elif method == 'update':
        requests.put(f'{api_url}//tasks', data=apt)
    elif method == 'delete':
        requests.delete(f'{api_url}//tasks', data=apt)
    return redirect(url_for('apartments.apartment', name=data.get('name')))
