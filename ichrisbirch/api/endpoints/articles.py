import json
import re

import httpx
import markdown
import pendulum
import structlog
from bs4 import BeautifulSoup
from bs4 import Tag
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status
from sqlalchemy import cast
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.ai.assistants.openai import OpenAIAssistant
from ichrisbirch.api.endpoints.auth import DbSession
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings
from ichrisbirch.util import clean_url

logger = structlog.get_logger()
router = APIRouter()


def _extract_video_id(url: str) -> str:
    """Extract YouTube video ID from any supported URL format.

    Handles youtube.com/watch?v=ID, youtu.be/ID, youtube.com/shorts/ID,
    and youtube.com/live/ID. Strips query parameters from the ID.
    """
    if 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0].split('&')[0]
    if 'youtube.com/shorts/' in url:
        return url.split('/shorts/')[1].split('?')[0].split('&')[0]
    if 'youtube.com/live/' in url:
        return url.split('/live/')[1].split('?')[0].split('&')[0]
    if 'v=' in url:
        return url.split('v=')[1].split('&')[0]
    raise ValueError(f'Cannot extract video ID from URL: {url}')


def _get_youtube_video_text_captions(url: str) -> str:
    video_id = _extract_video_id(url)
    yt_trans = YouTubeTranscriptApi()
    formatter = TextFormatter()
    transcript = yt_trans.fetch(video_id)
    return formatter.format_transcript(transcript)


def _get_formatted_title(soup: BeautifulSoup) -> str:
    """Extract and clean page title.

    Strips common site name suffixes separated by | or - (takes the first segment).
    """
    if not (soup.title and soup.title.string):
        logger.warning('article_title_parse_failed')
        return 'Could not parse title'

    title = soup.title.string.strip()

    # Strip site name suffixes: "Article Title | Site Name" or "Article Title - Site Name"
    # Split on the LAST separator to preserve titles that use these characters internally.
    for sep in (' | ', ' - ', ' — ', ' · '):
        if sep in title:
            parts = title.rsplit(sep, 1)
            if len(parts[1].split()) <= 4:
                title = parts[0]
            break

    return title.removesuffix(' - YouTube').strip()


def _strip_noise_tags(soup: BeautifulSoup) -> None:
    """Remove tags that contribute noise rather than content."""
    for tag_name in ('script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript', 'svg', 'form'):
        for tag in soup.find_all(tag_name):
            tag.decompose()
    noise_pattern = re.compile(r'comment|cookie|banner|popup|modal|sidebar|social|share|newsletter|advert', re.IGNORECASE)
    for attr in ('class', 'id'):
        for tag in soup.find_all(attrs={attr: noise_pattern}):
            if isinstance(tag, Tag):
                tag.decompose()


def _get_text_content_from_html(soup: BeautifulSoup) -> str:
    """Extract readable text from HTML, preserving paragraph structure.

    Tries <article> tag first (standard semantic container for main content),
    then falls back to <main>, then the full <body>. Strips noise tags before
    extraction to avoid navigation menus, footers, cookie banners, etc.
    """
    _strip_noise_tags(soup)

    found = soup.find('article') or soup.find('main') or soup.find('body')
    container = found if isinstance(found, Tag) else soup

    content_tags = ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'pre', 'li', 'figcaption', 'td', 'th', 'dt', 'dd')
    elements = container.find_all(content_tags)

    if not elements:
        return container.get_text(separator='\n\n', strip=True)

    blocks: list[str] = []
    for el in elements:
        text = el.get_text(strip=True)
        if text and len(text) > 1:
            blocks.append(text)

    return '\n\n'.join(blocks)


@router.get('/', response_model=list[schemas.Article], status_code=status.HTTP_200_OK)
async def read_many(
    session: DbSession,
    favorites: bool | None = None,
    archived: bool | None = None,
    unread: bool | None = None,
):
    query = select(models.Article).order_by(models.Article.title.asc())
    if favorites is True:
        # Use PostgreSQL's make_interval for proper SQL date arithmetic
        is_due_for_review = (models.Article.last_read_date.is_not(None)) & (
            models.Article.last_read_date + func.make_interval(0, 0, 0, models.Article.review_days) <= func.now()
        )
        query = query.where(models.Article.is_favorite.is_(True))
        query = query.where((models.Article.last_read_date.is_(None)) | is_due_for_review)
    if favorites is False:
        query = query.where(models.Article.is_favorite.is_(False))
    if archived is True:
        query = query.where(models.Article.is_archived.is_(True))
    if archived is False:
        query = query.where(models.Article.is_archived.is_(False))
    if unread is True:
        query = query.where(models.Article.last_read_date.is_(None))
    if unread is False:
        query = query.where(models.Article.last_read_date.is_not(None))
    return list(session.scalars(query).all())


@router.get('/current/', response_model=schemas.Article | None, status_code=status.HTTP_200_OK)
async def current(session: DbSession):
    query = select(models.Article).where(models.Article.is_current.is_(True))
    return session.scalars(query).first()


@router.get('/url/', response_model=schemas.Article, status_code=status.HTTP_200_OK)
async def read_one_url(url: str, session: DbSession):
    url = clean_url(url)
    if article := session.scalar(select(models.Article).where(models.Article.url == url)):
        return article
    raise NotFoundException('article', f'url={url}', logger)


@router.post('/', response_model=schemas.Article, status_code=status.HTTP_201_CREATED)
async def create(article: schemas.ArticleCreate, session: DbSession):
    obj = models.Article(**article.model_dump())
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def _summarize_and_create_article(url: str, notes: str | None, session: Session, settings: Settings) -> models.Article:
    """Fetch URL, summarize via OpenAI, create article.

    Used by create-from-url endpoint and bulk import worker.
    """
    url = clean_url(url)
    existing = session.scalar(select(models.Article).where(models.Article.url == url))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Article already exists: {url}')

    url_response = httpx.get(url, follow_redirects=True, headers=settings.mac_safari_request_headers)
    url_response.raise_for_status()
    soup = BeautifulSoup(url_response.content, 'html.parser')
    title = _get_formatted_title(soup)

    if 'youtube.com' in url or 'youtu.be' in url:
        text_content = _get_youtube_video_text_captions(url)
    else:
        text_content = _get_text_content_from_html(soup)

    assistant = OpenAIAssistant(
        name='Article Summary with Tags',
        instructions=settings.ai.prompts.article_summary_tags,
        response_format={'type': 'json_object'},
        settings=settings,
    )
    data = json.loads(assistant.generate(text_content))

    article = models.Article(
        title=title,
        url=url,
        tags=data.get('tags', []),
        summary=data.get('summary', ''),
        notes=notes,
        save_date=pendulum.now(),
        read_count=0,
        is_favorite=False,
        is_current=False,
        is_archived=False,
    )
    session.add(article)
    session.commit()
    session.refresh(article)
    logger.info('article_created_from_url', url=url, title=title)
    return article


@router.post('/create-from-url/', response_model=schemas.Article, status_code=status.HTTP_201_CREATED)
async def create_from_url(
    body: schemas.ArticleCreateFromUrl,
    session: DbSession,
    settings: Settings = Depends(get_settings),
):
    """Create an article from a URL. Automatically fetches content, summarizes via AI, and generates tags."""
    return _summarize_and_create_article(body.url, body.notes, session, settings)


@router.post('/bulk-import/', status_code=status.HTTP_202_ACCEPTED)
async def bulk_import(request: Request):
    """Enqueue URLs for bulk import. Returns batch_id for status polling."""
    from ichrisbirch.api.article_import_worker import enqueue_bulk_import

    body = await request.json()
    urls = body.get('urls', [])
    notes_map = body.get('notes', {})
    if not urls:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='No URLs provided')
    redis_client = request.app.state.redis_client
    batch_id = enqueue_bulk_import(redis_client, urls, notes_map)
    return {'batch_id': batch_id, 'total': len(urls), 'status': 'queued'}


@router.get('/bulk-import/{batch_id}/', status_code=status.HTTP_200_OK)
async def bulk_import_status(batch_id: str, request: Request):
    """Check status of a bulk article import batch."""
    from ichrisbirch.api.article_import_worker import get_batch_status

    redis_client = request.app.state.redis_client
    batch = get_batch_status(redis_client, batch_id)
    if batch is None:
        raise NotFoundException('batch', batch_id, logger)
    return batch


@router.get('/failed-imports/', response_model=list[schemas.ArticleFailedImport], status_code=status.HTTP_200_OK)
async def list_failed_imports(session: DbSession):
    """List all failed article imports."""
    query = select(models.ArticleFailedImport).order_by(models.ArticleFailedImport.failed_at.desc())
    return list(session.scalars(query).all())


@router.get('/search/', response_model=list[schemas.Article], status_code=status.HTTP_200_OK)
async def search(q: str, session: DbSession):
    """Search for comma-separated list of tags.

    Search terms must be separated and wildcards added.
    `tags` column must be converted from array to string to perform the like comparison for each search term.
    Use the OR to search for any of the specified search terms.
    NOTE: Converting the tags array to text cannot use the GIN index that is set in postgres on the tags column.
    This is a limitation of the array type in that it can't match partial results and use the index.
    """
    logger.debug('article_search', query=q)
    search_terms = [f'%{term.strip()}%' for term in q.split(',')]
    logger.debug('article_search_terms', terms=search_terms)
    conditions = [cast((models.Article.tags), postgresql.TEXT).ilike(term) for term in search_terms]
    articles = select(models.Article).filter(or_(*conditions)).order_by(models.Article.title.asc())
    results = session.scalars(articles).all()
    logger.debug('article_search_results', count=len(results))
    return list(results)


@router.post('/summarize/', response_model=schemas.ArticleSummary, status_code=status.HTTP_201_CREATED)
async def summarize(request: Request, settings: Settings = Depends(get_settings)):
    """Summarize youtube video or article based on the url.

    Return a summary of the article or video including title, summary, tags. If youtube video, use captions for video summary. If article,
    use html content for summary. Using openai chat to summarize and provide tags.
    """
    request_data = await request.json()
    logger.debug('article_summarize_request', data=request_data)
    url = clean_url(request_data.get('url'))
    url_response = httpx.get(url, follow_redirects=True, headers=settings.mac_safari_request_headers).raise_for_status()
    soup = BeautifulSoup(url_response.content, 'html.parser')
    title = _get_formatted_title(soup)
    logger.debug('article_title_retrieved', title=title)

    if 'youtube.com' in url or 'youtu.be' in url:
        text_content = _get_youtube_video_text_captions(url)
    else:
        text_content = _get_text_content_from_html(soup)

    assistant = OpenAIAssistant(
        name='Article Summary with Tags',
        instructions=settings.ai.prompts.article_summary_tags,
        response_format={'type': 'json_object'},
        settings=get_settings(),
    )
    data = json.loads(assistant.generate(text_content))
    return schemas.ArticleSummary(title=title, summary=data.get('summary'), tags=data.get('tags'))


@router.post('/insights/', response_model=None, status_code=status.HTTP_200_OK)
async def insights(request: Request, settings: Settings = Depends(get_settings)):
    """Summarize youtube video or article based on the url.

    Return a detailed summary, insights, and recommendations. If youtube video, use captions for video summary. If article, use html content
    for summary. Using openai chat to summarize and provide tags.
    """
    request_data = await request.json()
    logger.debug('article_insights_request', data=request_data)
    url = clean_url(request_data.get('url'))
    logger.debug('article_insights_processing', url=url)
    url_response = httpx.get(url, follow_redirects=True, headers=settings.mac_safari_request_headers).raise_for_status()
    soup = BeautifulSoup(url_response.content, 'html.parser')
    title = _get_formatted_title(soup)

    if 'youtube.com' in url or 'youtu.be' in url:
        try:
            logger.debug('youtube_captions_fetching')
            text_content = _get_youtube_video_text_captions(url)
        except Exception as e:
            logger.error('youtube_captions_error', url=url, error=str(e))
            # format error response into html
            lines = []
            for i, line in enumerate(str(e).strip().split('\n')):
                if i == 0:
                    lines.append(f'<h3>{line}</h3>')
                else:
                    lines.append(f'<p>{line}</p>')
            html = ''.join(lines).replace('<p></p>', '')
            return Response(content=html)  # must return status code 200 to avoid error in form javascript
    else:
        text_content = _get_text_content_from_html(soup)

    assistant = OpenAIAssistant(name='Article Insights', settings=settings, instructions=settings.ai.prompts.article_insights)
    mkd = assistant.generate(text_content)
    full_mkd = f'# {title}\n{mkd}'
    html = markdown.markdown(full_mkd)

    return Response(html)


@router.get('/stats/', response_model=schemas.ArticleStats, status_code=status.HTTP_200_OK)
async def stats(session: DbSession):
    """Return aggregated article statistics: summary counts, by-tag breakdown, save intake, and read frequency."""
    summary_row = session.execute(
        select(
            func.count().label('total'),
            func.count(models.Article.last_read_date).label('read'),
            func.count().filter(models.Article.is_favorite.is_(True)).label('favorites'),
            func.count().filter(models.Article.is_archived.is_(True)).label('archived'),
            func.count().filter(models.Article.is_current.is_(True)).label('current'),
        )
    ).one()
    summary = schemas.ArticleSummaryStats(
        total=summary_row.total,
        read=summary_row.read,
        unread=summary_row.total - summary_row.read,
        favorites=summary_row.favorites,
        archived=summary_row.archived,
        current=summary_row.current,
    )

    by_tag_rows = session.execute(
        select(
            func.unnest(models.Article.tags).label('tag'),
            func.count().label('total'),
            func.count(models.Article.last_read_date).label('read'),
        )
        .group_by(text('tag'))
        .order_by(func.count().desc())
    ).all()
    by_tag = [schemas.ArticleTagStat(tag=r.tag, total=r.total, read=r.read, unread=r.total - r.read) for r in by_tag_rows]

    saved_by_month_rows = session.execute(
        select(
            func.date_trunc('month', models.Article.save_date).label('month'),
            func.count().label('count'),
        )
        .group_by(text('month'))
        .order_by(text('month'))
    ).all()
    saved_by_month = [schemas.ArticleSavedByMonth(month=r.month.strftime('%Y-%m'), count=r.count) for r in saved_by_month_rows]

    frequently_read = list(
        session.scalars(select(models.Article).where(models.Article.read_count >= 2).order_by(models.Article.read_count.desc())).all()
    )

    return schemas.ArticleStats(
        summary=summary,
        by_tag=by_tag,
        saved_by_month=saved_by_month,
        frequently_read=frequently_read,
    )


@router.get('/{id}/', response_model=schemas.Article, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: DbSession):
    if article := session.get(models.Article, id):
        return article
    raise NotFoundException('article', id, logger)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: DbSession):
    if article := session.get(models.Article, id):
        session.delete(article)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise NotFoundException('article', id, logger)


@router.patch('/{id}/', response_model=schemas.Article, status_code=status.HTTP_200_OK)
async def update(id: int, update: schemas.ArticleUpdate, session: DbSession):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug('article_update', article_id=id, update_data=update_data)
    if article := session.get(models.Article, id):
        for attr, value in update_data.items():
            setattr(article, attr, value)
        session.commit()
        session.refresh(article)
        return article
    raise NotFoundException('article', id, logger)
