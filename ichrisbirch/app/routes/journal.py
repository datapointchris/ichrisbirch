import requests
from flask import Blueprint, redirect, render_template, request, url_for

from ichrisbirch.config import settings
from ichrisbirch.models.journal import JournalEntry

blueprint = Blueprint('journal', __name__, template_folder='templates/journal', static_folder='static')


@blueprint.route('/<int:id>/')
@blueprint.route('/')
def index(id=None):
    """Journal home endpoint"""
    if id:
        entry = requests.get(f'{settings.API_URL}/journal/{id}/', timeout=settings.REQUEST_TIMEOUT)
        return render_template('journal/index.html', entry=entry, entries=None)
    else:
        entries = requests.get(f'{settings.API_URL}/journal', timeout=settings.REQUEST_TIMEOUT)
        return render_template('journal/index.html', entry=None, entries=entries)


@blueprint.route('/entry/', methods=['GET', 'POST'])
def entry():
    """Journal entry endpoint"""
    if request.method == 'POST':
        entry = JournalEntry(**request.form)
        requests.post(f'{settings.API_URL}/journal', data=entry, timeout=settings.REQUEST_TIMEOUT)
        return redirect(url_for('journal.index'))

    return render_template('journal/entry.html')


@blueprint.route('/search/')
def search():
    """Endpoint to search for a journal entry"""
    search_text = request.form.get('search_text')
    results = requests.get(f'{settings.API_URL}/journal/search', data=search_text, timeout=settings.REQUEST_TIMEOUT)
    return render_template(
        'journal/search.html',
        results=results,
    )
