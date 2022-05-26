from flask import Blueprint, render_template, request, current_app, url_for, redirect
from ..models.journal import JournalEntry
import requests

blueprint = Blueprint(
    'journal', __name__, template_folder='templates/journal', static_folder='static'
)


@blueprint.route('/<int:id>/')
@blueprint.route('/')
def index(id=None):
    api_url = current_app.config.get('API_URL')
    if id:
        entry = requests.get(f'{api_url}/journal/{id}/')
        return render_template('journal/index.html', entry=entry, entries=None)
    else:
        entries = requests.get(f'{api_url}/journal')
        return render_template('journal/index.html', entry=None, entries=entries)


@blueprint.route('/entry/', methods=['GET', 'POST'])
def entry():
    api_url = current_app.config.get('API_URL')
    if request.method == 'POST':
        entry = JournalEntry(**request.form)
        response = requests.post(f'{api_url}/journal', data=entry)
        return redirect(url_for('journal.index'))

    return render_template('journal/entry.html')


@blueprint.route('/search/')
def search():
    api_url = current_app.config.get('API_URL')
    search_text = request.form.get('search_text')
    results = requests.get(f'{api_url}/journal/search', data=search_text)
    return render_template(
        'journal/search.html',
        results=results,
    )
