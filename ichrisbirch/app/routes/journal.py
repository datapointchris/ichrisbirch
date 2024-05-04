import httpx
from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from ichrisbirch.config import get_settings
from ichrisbirch.models.journal import JournalEntry

settings = get_settings()

blueprint = Blueprint('journal', __name__, template_folder='templates/journal', static_folder='static')


@blueprint.route('/<int:id>/')
@blueprint.route('/')
def index(id=None):
    """Journal home endpoint"""
    if id:
        entry = httpx.get(f'{settings.api_url}/journal/{id}/')
        return render_template('journal/index.html', entry=entry, entries=None)
    else:
        entries = httpx.get(f'{settings.api_url}/journal')
        return render_template('journal/index.html', entry=None, entries=entries)


@blueprint.route('/entry/', methods=['GET', 'POST'])
def entry():
    """Journal entry endpoint"""
    if request.method == 'POST':
        entry = JournalEntry(**request.form)
        httpx.post(f'{settings.api_url}/journal', data=entry)
        return redirect(url_for('journal.index'))

    return render_template('journal/entry.html')


@blueprint.route('/search/')
def search():
    """Endpoint to search for a journal entry"""
    search_text = request.form.get('search_text')
    results = httpx.get(f'{settings.api_url}/journal/search', data=search_text)
    return render_template(
        'journal/search.html',
        results=results,
    )
