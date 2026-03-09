import structlog
from fastapi import status
from flask import Blueprint
from flask import Response
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import login_required

from ichrisbirch import schemas
from ichrisbirch.api.client.exceptions import APIHTTPError
from ichrisbirch.api.client.logging_client import logging_flask_session_client
from ichrisbirch.app import forms

logger = structlog.get_logger()

blueprint = Blueprint('books', __name__, template_folder='templates/books', static_folder='static')


@blueprint.before_request
@login_required
def enforce_login():
    pass


@blueprint.context_processor
def inject_book_counts():
    """Inject book summary counts into the request context.

    Status priority: Sold (has sell_date) > Abandoned > Read > Reading > To Read.
    Sold is exclusive — a sold book is not counted in any other category.
    """
    base_url = current_app.config['SETTINGS'].api_url
    with logging_flask_session_client(base_url=base_url) as client:
        books_api = client.resource('books', schemas.Book)
        books = books_api.get_many()
        total_count = len(books)
        sold_count = sum(1 for b in books if b.sell_date)
        unsold = [b for b in books if not b.sell_date]
        abandoned_count = sum(1 for b in unsold if b.abandoned)
        read_count = sum(1 for b in unsold if b.read_finish_date and not b.abandoned)
        reading_count = sum(1 for b in unsold if b.read_start_date and not b.read_finish_date and not b.abandoned)
        to_read_count = sum(1 for b in unsold if not b.read_start_date and not b.abandoned)
        return dict(
            book_total_count=total_count,
            book_read_count=read_count,
            book_reading_count=reading_count,
            book_abandoned_count=abandoned_count,
            book_sold_count=sold_count,
            book_to_read_count=to_read_count,
        )


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    base_url = current_app.config['SETTINGS'].api_url
    with logging_flask_session_client(base_url=base_url) as client:
        books_api = client.resource('books', schemas.Book)
        if search := request.args.get('search'):
            books = books_api.get_many('search', params={'q': search})
        else:
            books = books_api.get_many()
        return render_template('books/index.html', books=books)


@blueprint.route('/add/', methods=['GET', 'POST'])
def add():
    create_form = forms.BookCreateForm()
    return render_template('books/add.html', create_form=create_form)


@blueprint.route('/goodreads-info/', methods=['POST'])
def goodreads_info():
    """Proxy endpoint for Goodreads book info lookup.

    JavaScript calls this Flask endpoint, which forwards to the API with user's session credentials.
    """
    data = request.get_json()
    isbn = data.get('isbn') if data else None
    if not isbn:
        return Response('Missing ISBN', status=400)

    settings = current_app.config['SETTINGS']
    with logging_flask_session_client(base_url=settings.api_url) as client:
        goodreads_api = client.resource('books/goodreads', schemas.BookGoodreadsInfo)
        if result := goodreads_api.post(json={'isbn': isbn}):
            return {'title': result.title, 'author': result.author, 'tags': result.tags, 'goodreads_url': result.goodreads_url}
        return Response('Failed to get Goodreads info', status=500)


@blueprint.route('/edit/<int:book_id>/', methods=['GET'])
def edit(book_id):
    base_url = current_app.config['SETTINGS'].api_url
    with logging_flask_session_client(base_url=base_url) as client:
        books_api = client.resource('books', schemas.Book)
        book = books_api.get_one(book_id)
        update_form = forms.BookUpdateForm(obj=book, data={'tags': ', '.join(book.tags)})
        return render_template('books/edit.html', book=book, update_form=update_form)


@blueprint.route('/crud/', methods=['POST'])
def crud():
    base_url = current_app.config['SETTINGS'].api_url
    with logging_flask_session_client(base_url=base_url) as client:
        books_api = client.resource('books', schemas.Book)
        data = request.form.to_dict()
        action = data.pop('action')

        match action:
            case 'add':
                form = forms.BookCreateForm(request.form)
                if form.validate_on_submit():
                    existing = None
                    if data.get('isbn'):
                        try:
                            existing = books_api.get_one(f'isbn/{data["isbn"]}')
                        except APIHTTPError as e:
                            if e.status_code == 404:
                                existing = None
                            else:
                                raise
                    if existing:
                        flash(f'already exists: {data["isbn"]}', 'warning')
                        logger.warning('book_already_exists', isbn=data['isbn'])
                    else:
                        # convert string field of tags to list for storing in postgres array
                        data['tags'] = [tag.strip().lower() for tag in data['tags'].split(',')]
                        if not data.get('isbn'):
                            data['isbn'] = None
                        books_api.post(json=data)
                        flash(f'Added: {data["title"]}', 'success')
                else:
                    flash('Form validation failed', 'error')
                    logger.warning('book_form_validation_failed', errors=form.errors)
                    for field, errors in form.errors.items():
                        for error in errors:
                            flash(f'{field}: {error}', 'error')
            case 'edit':
                book_id = data.pop('id')
                form = forms.BookUpdateForm(request.form)
                if form.validate_on_submit():
                    if data.get('tags'):
                        data['tags'] = [tag.strip().lower() for tag in data['tags'].split(',')]
                    else:
                        data['tags'] = []
                    books_api.patch(book_id, json=data)
                    flash(f'Updated: {data.get("title", "")}', 'success')
                else:
                    flash('Form validation failed', 'error')
                    logger.warning('book_edit_form_validation_failed', errors=form.errors)
                    for field, errors in form.errors.items():
                        for error in errors:
                            flash(f'{field}: {error}', 'error')
                    return redirect(url_for('books.edit', book_id=book_id))

            case 'delete':
                books_api.delete(data.get('id'))

            case _:
                return Response(f'Method/Action {action} not allowed', status=status.HTTP_405_METHOD_NOT_ALLOWED)

        return redirect(request.referrer or url_for('books.index'))
