import logging
import random

import httpx
import pendulum
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
from ichrisbirch.app import forms
from ichrisbirch.app.query_api import QueryAPI
from ichrisbirch.config import Settings

logger = logging.getLogger(__name__)

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
        logger.info('found text data')
        urls.extend(line.strip() for line in data['text'].splitlines())
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            logger.info('found file data')
            urls.extend(line.decode('utf-8').strip() for line in file)
    return urls


def add_bulk_article(articles_api, summarize_api, url: str, settings: Settings):
    """Add article using summarize endpoint to auto generate summary and tags for the bulk endpoint."""
    logger.info(f'processing: {url}')
    if articles_api.get_one('url', params={'url': url}):
        raise ValueError(f'already exists: {url}')
    httpx.get(url, follow_redirects=True, headers=settings.mac_safari_request_headers).raise_for_status()
    openai_summary = summarize_api.post(json={'url': url}, timeout=20)
    article = dict(
        title=openai_summary.title,
        url=url,
        tags=openai_summary.tags,
        summary=openai_summary.summary,
        save_date=str(pendulum.now()),
    )
    articles_api.post(json=article)
    logger.info(f'created: {url}')


def bulk_add_articles(articles_api, summarize_api, urls: list[str], settings: Settings):
    """Add all articles in url list.

    Each url is tried twice, sometimes a delayed response from openai causes a failure.
    """
    added: list[str] = []
    errors: list[tuple[str, str]] = []
    for url in urls:
        try:
            add_bulk_article(articles_api, summarize_api, url, settings)
            added.append(url)
        except ValueError as e:
            logger.warning(e)
            errors.append((url, str(e)))
        except Exception as e:
            logger.warning(f'error processing: {url}')
            logger.warning(e)
            errors.append((url, str(e)))
    return added, errors


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    articles_api = QueryAPI(base_endpoint='articles', response_model=schemas.Article)
    if not (article := articles_api.get_one('current')):
        logger.warning('no current article')
        # TODO: [2024/06/07] - Get user preference for current articles, whether to filter only unread
        # or include favorites
        # unread_only = current_user.preferences.articles.get('only_unread_for_new_current')
        # include_favorites = current_user.preferences.articles.get('include_favorites_for_new_current')
        if article := make_random_article_current(articles_api):
            logger.info(f"made article '{article.title}' current")
        else:
            logger.info('no articles')
    return render_template('articles/index.html', article=article)


@blueprint.route('/all/', methods=['GET'])
def all():
    articles_api = QueryAPI(base_endpoint='articles', response_model=schemas.Article)
    articles = articles_api.get_many()
    return render_template('articles/all.html', articles=articles)


@blueprint.route('/add/', methods=['GET', 'POST'])
def add():
    settings = current_app.config['SETTINGS']
    create_form = forms.ArticleCreateForm()
    summary_endpoint = f'{settings.api_url}/articles/summarize/'
    return render_template('articles/add.html', create_form=create_form, summary_endpoint=summary_endpoint)


@blueprint.route('/bulk-add/', methods=['GET', 'POST'])
def bulk_add():
    settings = current_app.config['SETTINGS']
    return render_template('articles/bulk-add.html', settings=settings)


@blueprint.route('/bulk-add-results/', methods=['GET', 'POST'])
def bulk_add_results():
    return render_template('articles/bulk-add-results.html')


@blueprint.route('/insights/', methods=['GET', 'POST'])
def insights():
    settings = current_app.config['SETTINGS']
    insights_endpoint = f'{settings.api_url}/articles/insights/'
    if request.method.upper() == 'POST':
        url = request.form.get('url')
        start = pendulum.now()
        response = httpx.post(insights_endpoint, json={'url': url}, timeout=30)
        elapsed = (pendulum.now() - start).in_words()
        article_insights = response.text
        submitted_url = url
    else:
        article_insights, submitted_url, elapsed = '', '', ''
    return render_template('articles/insights.html', submitted_url=submitted_url, article_insights=article_insights, elapsed=elapsed)


@blueprint.route('/search/', methods=['GET', 'POST'])
def search():
    articles = []
    if request.method.upper() == 'POST':
        articles_api = QueryAPI(base_endpoint='articles', response_model=schemas.Article)
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
    settings = current_app.config['SETTINGS']
    articles_api = QueryAPI(base_endpoint='articles', response_model=schemas.Article)
    summarize_api = QueryAPI(base_endpoint='articles/summarize', response_model=schemas.ArticleSummary)
    data = request.form.to_dict()
    action = data.pop('action')

    match action:
        case 'add':
            form = forms.ArticleCreateForm(request.form)
            if form.validate_on_submit():
                if articles_api.get_one('url', params={'url': data['url']}):
                    message = f'already exists: {data["url"]}'
                    flash(message, 'warning')
                    logger.warning(message)
                else:
                    # convert string field of tags to list for storing in postgres array
                    data['tags'] = [tag.strip().lower() for tag in data['tags'].split(',')]
                    data['save_date'] = str(pendulum.now())
                    articles_api.post(json=data)
        case 'bulk_add':
            if urls := process_bulk_urls(request, data):
                succeeded, errored = bulk_add_articles(articles_api, summarize_api, urls, settings)
            else:
                flash('No URLs provided', 'warning')
            succeeded_articles = '\n'.join([article.strip() for article in succeeded])
            errored_articles = '\n'.join([article[0].strip() for article in errored])
            errored_debug = '\n\n'.join([f'{article[0].strip()}\n{article[1].strip()}' for article in errored])
            return render_template(
                'articles/bulk-add-results.html',
                succeeded_articles=succeeded_articles,
                errored_articles=errored_articles,
                errored_debug=errored_debug,
            )
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
