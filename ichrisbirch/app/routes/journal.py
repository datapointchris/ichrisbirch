import requests
from flask import Blueprint, redirect, render_template, request, url_for

from ichrisbirch import settings
from ichrisbirch.models.journal import JournalEntry

blueprint = Blueprint('journal', __name__, template_folder='templates/journal', static_folder='static')


@blueprint.route('/<int:id>/')
@blueprint.route('/')
def index(id=None):
    """Journal home endpoint"""
    api_url = settings.API_URL
    if id:
        entry = requests.get(f'{api_url}/journal/{id}/')
        return render_template('journal/index.html', entry=entry, entries=None)
    else:
        entries = requests.get(f'{api_url}/journal')
        return render_template('journal/index.html', entry=None, entries=entries)


@blueprint.route('/entry/', methods=['GET', 'POST'])
def entry():
    """Journal entry endpoint"""
    api_url = settings.API_URL
    if request.method == 'POST':
        entry = JournalEntry(**request.form)
        requests.post(f'{api_url}/journal', data=entry)
        return redirect(url_for('journal.index'))

    return render_template('journal/entry.html')


@blueprint.route('/search/')
def search():
    """Endpoint to search for a journal entry"""
    api_url = settings.API_URL
    search_text = request.form.get('search_text')
    results = requests.get(f'{api_url}/journal/search', data=search_text)
    return render_template(
        'journal/search.html',
        results=results,
    )
