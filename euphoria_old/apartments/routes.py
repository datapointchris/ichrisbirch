from flask import Blueprint, redirect, render_template, request, url_for, current_app
from euphoria.apartments.models import Apartment, Feature
import os
import requests

apartments_bp = Blueprint(
    'apartments_bp',
    __name__,
    template_folder='templates/apartments',
    static_folder='static',
)

@apartments_bp.route('/')
def apartments():
    apartments = [apt for apt in Apartment.scan()]
    return render_template(
        'apartments.html',
        apartments=apartments,
        apartment=None,
        features=None,
        message='No apartment selected',
    )


@apartments_bp.route('/<string:name>/')
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
@apartments_bp.route('/edit/')
def noedit():
    apartments = [apt for apt in Apartment.scan()]
    return render_template(
        'apartments.html',
        apartments=apartments,
        apartment=None,
        features=None,
        message='No apartment selected',
    )


@apartments_bp.route('/edit/<string:name>/')
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


@apartments_bp.route('/form/', methods=['POST'])
def crud():
    api_url = current_app.config.get('API_URL')
    data = request.form.to_dict()
    method = data.pop('method')
    apt = Apartment(**data)
    if method == 'add':
        response = requests.post(f'{api_url}/tasks', data=apt)
    elif method == 'update':
        response = requests.put(f'{api_url}//tasks', data=apt)
    elif method == 'delete':
        response = requests.delete(f'{api_url}//tasks', data=apt)
    return redirect(url_for('apartments_bp.apartment', name=data.get('name')))
