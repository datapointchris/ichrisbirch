import logging

import pendulum
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
from ichrisbirch.app import forms
from ichrisbirch.app.query_api import QueryAPI
from ichrisbirch.config import get_settings

logger = logging.getLogger('app.books')
settings = get_settings()
blueprint = Blueprint('books', __name__, template_folder='templates/books', static_folder='static')


@blueprint.before_request
@login_required
def enforce_login():
    pass


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    books_api = QueryAPI(base_url='books', logger=logger, response_model=schemas.Book)
    books = books_api.get_many()
    return render_template('books/index.html', books=books)


@blueprint.route('/add/', methods=['GET', 'POST'])
def add():
    create_form = forms.BookCreateForm()
    goodreads_info_endpoint = f'{settings.api_url}/books/goodreads/'
    return render_template('books/add.html', create_form=create_form, goodreads_info_endpoint=goodreads_info_endpoint)


@blueprint.route('/crud/', methods=['POST'])
def crud():
    books_api = QueryAPI(base_url='books', logger=logger, response_model=schemas.Book)
    data = request.form.to_dict()
    action = data.pop('action')

    match action:
        case 'add':
            form = forms.BookCreateForm(request.form)
            if form.validate_on_submit():
                if books_api.get_one(f'isbn/{data['isbn']}'):
                    message = f'already exists: {data["isbn"]}'
                    flash(message, 'warning')
                    logger.warning(message)
                else:
                    # convert string field of tags to list for storing in postgres array
                    data['tags'] = [tag.strip().lower() for tag in data['tags'].split(',')]
                    books_api.post(json=data)
                    flash(f'Added: {data['title']}', 'success')
            else:
                message = 'Form validation failed'
                flash(message, 'error')
                logger.warning(message)
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'{field}: {error}', 'error')
                        logger.warning(f'{field}: {error}')
        case 'archive':
            books_api.patch(data.get('id'), json={'is_archived': True})
        case 'unarchive':
            books_api.patch(data.get('id'), json={'is_archived': False})
        case 'make_current':
            books_api.patch(data.get('id'), json={'is_current': True})
        case 'remove_current':
            books_api.patch(data.get('id'), json={'is_current': False})
        case 'make_favorite':
            books_api.patch(data.get('id'), json={'is_favorite': True})
        case 'unfavorite':
            books_api.patch(data.get('id'), json={'is_favorite': False})
        case 'mark_read':
            if article := books_api.get_one(data.get('id')):
                books_api.patch(
                    data.get('id'),
                    json={
                        'is_current': False,
                        'is_archived': True,
                        'last_read_date': str(pendulum.now()),
                        'read_count': article.read_count + 1,
                    },
                )
        case 'delete':
            books_api.delete(data.get('id'))
        case 'search':
            books = books_api.get_many('search', params={'q': data.get('search_text')})
            return render_template('books/index.html', books=books)

        case _:
            return Response(f'Method/Action {action} not allowed', status=status.HTTP_405_METHOD_NOT_ALLOWED)

    return redirect(request.referrer or url_for('books.index'))
