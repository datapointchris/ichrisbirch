import random

import pendulum
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

blueprint = Blueprint('articles', __name__, template_folder='templates/articles', static_folder='static')


@blueprint.before_request
@login_required
def enforce_login():
    pass


def make_random_article_current(articles_api, unread=True, favorites=False):
    params = {'archived': False, 'unread': unread, 'favorites': favorites}
    if not (articles := articles_api.get_many(params=params)):
        return None
    article_id = random.choice(articles).id
    new_current_article = articles_api.patch(article_id, json={'is_current': True})
    return new_current_article


def process_bulk_urls(request, data):
    urls = []
    if 'text' in data:
        logger.info('bulk_urls_text_data_found')
        urls.extend(line.strip() for line in data['text'].splitlines())
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            logger.info('bulk_urls_file_data_found', filename=file.filename)
            urls.extend(line.decode('utf-8').strip() for line in file)
    return urls


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    settings = current_app.config['SETTINGS']
    with logging_flask_session_client(base_url=settings.api_url) as client:
        articles_api = client.resource('articles', schemas.Article)
        if not (article := articles_api.get_one('current')):
            logger.warning('no_current_article')
            # TODO: [2024/06/07] - Get user preference for current articles, whether to filter only unread
            # or include favorites
            # unread_only = current_user.preferences.articles.get('only_unread_for_new_current')
            # include_favorites = current_user.preferences.articles.get('include_favorites_for_new_current')
            if article := make_random_article_current(articles_api):
                logger.info('article_made_current', title=article.title)
            else:
                logger.info('no_articles_available')
        return render_template('articles/index.html', article=article)


@blueprint.route('/all/', methods=['GET'])
def all():
    settings = current_app.config['SETTINGS']
    with logging_flask_session_client(base_url=settings.api_url) as client:
        articles_api = client.resource('articles', schemas.Article)
        articles = articles_api.get_many()
        return render_template('articles/all.html', articles=articles)


@blueprint.route('/add/', methods=['GET', 'POST'])
def add():
    create_form = forms.ArticleCreateForm()
    return render_template('articles/add.html', create_form=create_form)


@blueprint.route('/summarize-proxy/', methods=['POST'])
def summarize_proxy():
    """Proxy endpoint for article summarization.

    JavaScript calls this Flask endpoint, which forwards to the API with user's session credentials.
    """
    data = request.get_json()
    url = data.get('url') if data else None
    if not url:
        return Response('Missing URL', status=400)

    settings = current_app.config['SETTINGS']
    with logging_flask_session_client(base_url=settings.api_url) as client:
        summarize_api = client.resource('articles/summarize', schemas.ArticleSummary)
        if result := summarize_api.post(json={'url': url}):
            return {'title': result.title, 'summary': result.summary, 'tags': result.tags}
        return Response('Failed to summarize article', status=500)


@blueprint.route('/bulk-add/', methods=['GET', 'POST'])
def bulk_add():
    settings = current_app.config['SETTINGS']
    return render_template('articles/bulk-add.html', settings=settings)


@blueprint.route('/bulk-add-results/', methods=['GET'])
def bulk_add_results():
    batch_id = request.args.get('batch_id')
    return render_template('articles/bulk-add-results.html', batch_id=batch_id)


@blueprint.route('/bulk-import-status/', methods=['GET'])
def bulk_import_status():
    """Proxy endpoint for polling bulk import status from JavaScript."""
    batch_id = request.args.get('batch_id')
    if not batch_id:
        return Response('Missing batch_id', status=400)
    settings = current_app.config['SETTINGS']
    with logging_flask_session_client(base_url=settings.api_url) as client:
        status_api = client.resource(f'articles/bulk-import/{batch_id}', None)
        result = status_api.get_generic()
        if result:
            return result
        return Response('Batch not found', status=404)


@blueprint.route('/insights/', methods=['GET', 'POST'])
def insights():
    if request.method.upper() == 'POST':
        url = request.form.get('url')
        start = pendulum.now()
        settings = current_app.config['SETTINGS']
        with logging_flask_session_client(base_url=settings.api_url) as client:
            insights_api = client.resource('articles/insights', schemas.Article)
            response = insights_api.post_action(json={'url': url}, timeout=120)
            elapsed = (pendulum.now() - start).in_words()
            article_insights = response.text if response else ''
            submitted_url = url
    else:
        article_insights, submitted_url, elapsed = '', '', ''
    return render_template('articles/insights.html', submitted_url=submitted_url, article_insights=article_insights, elapsed=elapsed)


@blueprint.route('/search/', methods=['GET', 'POST'])
def search():
    articles = []
    if request.method.upper() == 'POST':
        settings = current_app.config['SETTINGS']
        with logging_flask_session_client(base_url=settings.api_url) as client:
            articles_api = client.resource('articles', schemas.Article)
            data = request.form.to_dict()
            search_text = data.get('search_text')
            logger.debug('article_search', referrer=request.referrer, search_text=search_text)
            if not search_text:
                flash('No search terms provided', 'warning')
            else:
                articles = articles_api.get_many('search', params={'q': search_text})
    return render_template('articles/search.html', articles=articles)


@blueprint.route('/crud/', methods=['POST'])
def crud():
    settings = current_app.config['SETTINGS']
    with logging_flask_session_client(base_url=settings.api_url) as client:
        articles_api = client.resource('articles', schemas.Article)
        data = request.form.to_dict()
        action = data.pop('action')

        match action:
            case 'add':
                form = forms.ArticleCreateForm(request.form)
                if form.validate_on_submit():
                    try:
                        existing = articles_api.get_one('url', params={'url': data['url']})
                    except APIHTTPError as e:
                        if e.status_code == 404:
                            existing = None
                        else:
                            raise
                    if existing:
                        flash(f'already exists: {data["url"]}', 'warning')
                        logger.warning('article_already_exists', url=data['url'])
                    else:
                        # convert string field of tags to list for storing in postgres array
                        data['tags'] = [tag.strip().lower() for tag in data['tags'].split(',')]
                        data['save_date'] = str(pendulum.now())
                        articles_api.post(json=data)
            case 'bulk_add':
                if urls := process_bulk_urls(request, data):
                    bulk_api = client.resource('articles/bulk-import', None)
                    result = bulk_api.post_action(json={'urls': urls})
                    if result and result.status_code == 202:
                        batch_id = result.json().get('batch_id')
                        return redirect(url_for('articles.bulk_add_results', batch_id=batch_id))
                    flash('Failed to submit bulk import', 'danger')
                else:
                    flash('No URLs provided', 'warning')
                return redirect(url_for('articles.bulk_add'))
            case 'archive':
                articles_api.patch(data.get('id'), json={'is_archived': True})
            case 'unarchive':
                articles_api.patch(data.get('id'), json={'is_archived': False})
            case 'make_current':
                articles_api.patch(data.get('id'), json={'is_current': True})
            case 'remove_current':
                articles_api.patch(data.get('id'), json={'is_current': False})
            case 'make_favorite':
                articles_api.patch(data.get('id'), json={'is_favorite': True})
            case 'unfavorite':
                articles_api.patch(data.get('id'), json={'is_favorite': False})
            case 'mark_read':
                if article := articles_api.get_one(data.get('id')):
                    articles_api.patch(
                        data.get('id'),
                        json={
                            'is_current': False,
                            'is_archived': True,
                            'last_read_date': str(pendulum.now()),
                            'read_count': article.read_count + 1,
                        },
                    )
            case 'delete':
                articles_api.delete(data.get('id'))

            case _:
                return Response(f'Method/Action {action} not allowed', status=status.HTTP_405_METHOD_NOT_ALLOWED)

        return redirect(request.referrer or url_for('articles.all'))
