import structlog
from flask import Blueprint
from flask import current_app
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import login_required

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.client.logging_client import logging_flask_session_client

logger = structlog.get_logger()
blueprint = Blueprint('journal', __name__, template_folder='templates/journal', static_folder='static')


@blueprint.before_request
@login_required
def enforce_login():
    pass


@blueprint.route('/<int:id>/')
@blueprint.route('/')
def index(id=None):
    """Journal home endpoint."""
    settings = current_app.config['SETTINGS']
    with logging_flask_session_client(base_url=settings.api_url) as client:
        journal_api = client.resource('journal', schemas.JournalEntry)
        if id:
            entry = journal_api.get_one(id)
            return render_template('journal/index.html', entry=entry, entries=None)
        else:
            entries = journal_api.get_many()
            return render_template('journal/index.html', entry=None, entries=entries)


@blueprint.route('/entry/', methods=['GET', 'POST'])
def entry():
    """Journal entry endpoint."""
    if request.method.upper() == 'POST':
        settings = current_app.config['SETTINGS']
        with logging_flask_session_client(base_url=settings.api_url) as client:
            journal_api = client.resource('journal', schemas.JournalEntry)
            entry_data = models.JournalEntry(**request.form)
            journal_api.post(data=entry_data)
            return redirect(url_for('journal.index'))

    return render_template('journal/entry.html')


@blueprint.route('/search/')
def search():
    """Endpoint to search for a journal entry."""
    settings = current_app.config['SETTINGS']
    with logging_flask_session_client(base_url=settings.api_url) as client:
        journal_api = client.resource('journal', schemas.JournalEntry)
        search_text = request.form.get('search_text')
        results = journal_api.get_many('search', data=search_text)
        return render_template('journal/search.html', results=results)
