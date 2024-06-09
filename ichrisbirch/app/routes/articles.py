import logging
import random

import httpx
import pendulum
from fastapi import status
from flask import Blueprint
from flask import Response
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from ichrisbirch import schemas
from ichrisbirch.app import forms
from ichrisbirch.app.query_api import QueryAPI
from ichrisbirch.config import get_settings

logger = logging.getLogger('app.articles')
blueprint = Blueprint('articles', __name__, template_folder='templates/articles', static_folder='static')
articles_api = QueryAPI(base_url='articles', logger=logger, response_model=schemas.Article)
summarize_api = QueryAPI(base_url='articles/summarize', logger=logger, response_model=schemas.ArticleSummary)
settings = get_settings()


def make_random_article_current(unread=True, favorites=False):
    params = {'archived': False, 'unread': unread, 'favorites': favorites}
    if not (articles := articles_api.get_many(params=params)):
        return None
    article_id = random.choice(articles).id
    new_current_article = articles_api.patch(article_id, json={'is_current': True})
    return new_current_article


def process_bulk_urls(request, data):
    urls = []
    if 'text' in data:
        logger.info('found text data')
        urls.extend(line.strip() for line in data['text'].splitlines())
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            logger.info('found file data')
            urls.extend(line.decode('utf-8').strip() for line in file)
    return urls


def add_article(url: str):
    """Add article using summarize endpoint to auto generate summary and tags."""
    logger.info(f'processing: {url}')
    httpx.get(url, follow_redirects=True).raise_for_status()
    openai_summary = summarize_api.post(json={'url': url}, timeout=10)
    article = dict(
        title=openai_summary.title,
        url=url,
        tags=openai_summary.tags,
        summary=openai_summary.summary,
        save_date=str(pendulum.now()),
    )
    articles_api.post(json=article)
    logger.info(f'created: {url}')
    flash(f'Created: {openai_summary.title}', 'success')


def bulk_add_articles(urls: list[str]):
    """Add all articles in url list.

    Each url is tried twice, sometimes a delayed response from openai causes a failure.
    """
    errors = []
    fatal = []
    for url in urls:
        try:
            add_article(url)
        except Exception as e:
            logger.error(f'error processing: {url}')
            logger.error(e)
            errors.append(url)
    if errors:
        logger.info('retrying urls with errors')
        for url in errors:
            try:
                add_article(url)
            except Exception as e:
                flash(f'error processing: {url}', 'error')
                logger.error(f'error processing: {url}')
                logger.error(e)
                flash(str(e), 'error')
                fatal.append(url)
    if fatal:
        for url in fatal:
            logger.warning(f'fatal: {url}')


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    if not (article := articles_api.get_one('current')):
        logger.warning('no current article')
        # TODO: [2024/06/07] - Get user preference for current articles, whether to filter only unread
        # or include favorites
        # unread_only = current_user.preferences.articles.get('only_unread_for_new_current')
        # include_favorites = current_user.preferences.articles.get('include_favorites_for_new_current')
        if article := make_random_article_current():
            logger.info(f"made article '{article.title}' current")
        else:
            logger.info('no articles')
    return render_template('articles/index.html', article=article)


@blueprint.route('/all/', methods=['GET'])
def all():
    articles = articles_api.get_many()
    return render_template('articles/all.html', articles=articles)


@blueprint.route('/add/', methods=['GET', 'POST'])
def add():
    create_form = forms.ArticleCreateForm()
    summary_endpoint = f'{settings.api_url}/articles/summarize/'
    return render_template('articles/add.html', create_form=create_form, summary_endpoint=summary_endpoint)


@blueprint.route('/bulk-add/', methods=['GET', 'POST'])
def bulk_add():
    return render_template('articles/bulk-add.html')


@blueprint.route('/search/', methods=['GET', 'POST'])
def search():
    articles = []
    if request.method == 'POST':
        data = request.form.to_dict()
        search_text = data.get('search_text')
        logger.debug(f'{request.referrer=} | {search_text=}')
        if not search_text:
            flash('No search terms provided', 'warning')
        else:
            articles = articles_api.get_many('search', params={'q': search_text})
    return render_template('articles/search.html', articles=articles)


@blueprint.route('/crud/', methods=['POST'])
def crud():
    data = request.form.to_dict()
    action = data.pop('action')

    match action:
        case 'add':
            form = forms.ArticleCreateForm(request.form)
            if form.validate_on_submit():
                # convert string field of tags to list for storing in postgres array
                data['tags'] = [tag.strip().lower() for tag in data['tags'].split(',')]
                data['save_date'] = str(pendulum.now())
                articles_api.post(json=data)
        case 'bulk_add':
            if urls := process_bulk_urls(request, data):
                bulk_add_articles(urls)
            else:
                flash('No URLs provided', 'warning')
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
