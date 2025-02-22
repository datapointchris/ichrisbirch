import logging

import httpx
from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import login_required

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.app.query_api import QueryAPI
from ichrisbirch.config import settings

logger = logging.getLogger('app.journal')
blueprint = Blueprint('journal', __name__, template_folder='templates/journal', static_folder='static')


@blueprint.before_request
@login_required
def enforce_login():
    pass


@blueprint.route('/<int:id>/')
@blueprint.route('/')
def index(id=None):
    """Journal home endpoint."""
    journal_api = QueryAPI(base_url='journal', logger=logger, response_model=schemas.JournalEntry)
    if id:
        entry = journal_api.get_one(id)
        return render_template('journal/index.html', entry=entry, entries=None)
    else:
        entries = httpx.get(f'{settings.api_url}/journal')
        return render_template('journal/index.html', entry=None, entries=entries)


@blueprint.route('/entry/', methods=['GET', 'POST'])
def entry():
    """Journal entry endpoint."""
    if request.method == 'POST':
        journal_api = QueryAPI(base_url='journal', logger=logger, response_model=schemas.JournalEntry)
        entry = models.JournalEntry(**request.form)
        journal_api.post(data=entry)
        return redirect(url_for('journal.index'))

    return render_template('journal/entry.html')


@blueprint.route('/search/')
def search():
    """Endpoint to search for a journal entry."""
    journal_api = QueryAPI(base_url='journal', logger=logger, response_model=schemas.JournalEntry)
    search_text = request.form.get('search_text')
    results = journal_api.get_many('search', data=search_text)
    return render_template('journal/search.html', results=results)
