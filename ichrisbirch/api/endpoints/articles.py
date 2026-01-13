import json

import httpx
import markdown
import structlog
from bs4 import BeautifulSoup
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from fastapi import status
from sqlalchemy import cast
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.ai.assistants.openai import OpenAIAssistant
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings
from ichrisbirch.database.session import get_sqlalchemy_session

logger = structlog.get_logger()
router = APIRouter()


def _get_youtube_video_text_captions(url: str) -> str:
    yt_trans = YouTubeTranscriptApi()
    formatter = TextFormatter()
    video_id = url.split('v=')[1]
    transcript = yt_trans.fetch(video_id)
    formatted = formatter.format_transcript(transcript)
    return formatted


def _get_formatted_title(soup: BeautifulSoup) -> str:
    if soup.title and soup.title.string:
        title = soup.title.string.split('|')[0].replace('...', '')
        title = title.removesuffix(' - YouTube').strip()
    else:
        logger.warning('article_title_parse_failed')
        title = 'Could not parse title'
    return title


def _get_text_content_from_html(soup: BeautifulSoup) -> str:
    relevant_content_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'li']
    tag_content = soup.find_all(relevant_content_tags)
    text_content = ' '.join(tag.get_text() for tag in tag_content)
    return text_content


@router.get('/', response_model=list[schemas.Article], status_code=status.HTTP_200_OK)
async def read_many(
    favorites: bool | None = None,
    archived: bool | None = None,
    unread: bool | None = None,
    session: Session = Depends(get_sqlalchemy_session),
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
async def current(session: Session = Depends(get_sqlalchemy_session)):
    query = select(models.Article).where(models.Article.is_current.is_(True))
    return session.scalars(query).first()


@router.get('/url/', response_model=schemas.Article, status_code=status.HTTP_200_OK)
async def read_one_url(url: str, session: Session = Depends(get_sqlalchemy_session)):
    if article := session.scalar(select(models.Article).where(models.Article.url == url)):
        return article
    raise NotFoundException('article', f'url={url}', logger)


@router.post('/', response_model=schemas.Article, status_code=status.HTTP_201_CREATED)
async def create(article: schemas.ArticleCreate, session: Session = Depends(get_sqlalchemy_session)):
    obj = models.Article(**article.model_dump())
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.get('/search/', response_model=list[schemas.Article], status_code=status.HTTP_200_OK)
async def search(q: str, session: Session = Depends(get_sqlalchemy_session)):
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
    url = request_data.get('url')
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
    url = request_data.get('url')
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


@router.get('/{id}/', response_model=schemas.Article, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if article := session.get(models.Article, id):
        return article
    raise NotFoundException('article', id, logger)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if article := session.get(models.Article, id):
        session.delete(article)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise NotFoundException('article', id, logger)


@router.patch('/{id}/', response_model=schemas.Article, status_code=status.HTTP_200_OK)
async def update(id: int, update: schemas.ArticleUpdate, session: Session = Depends(get_sqlalchemy_session)):
    update_data = update.model_dump(exclude_unset=True)
    logger.debug('article_update', article_id=id, update_data=update_data)
    if article := session.get(models.Article, id):
        for attr, value in update_data.items():
            setattr(article, attr, value)
        session.commit()
        session.refresh(article)
        return article
    raise NotFoundException('article', id, logger)
