import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter
from fastapi import Body
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from openai import OpenAI
from sqlalchemy import cast
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.config import get_settings
from ichrisbirch.database.sqlalchemy.session import get_sqlalchemy_session

logger = logging.getLogger('api.articles')
router = APIRouter()
settings = get_settings()


def IDNotFoundError(id: int):
    message = f'article {id} not found'
    logger.warning(message)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get('/', response_model=list[schemas.Article], status_code=status.HTTP_200_OK)
async def read_many(
    favorites: Optional[bool] = None,
    archived: Optional[bool] = None,
    unread: Optional[bool] = None,
    session: Session = Depends(get_sqlalchemy_session),
):
    query = select(models.Article).order_by(models.Article.title.asc())
    if favorites is True:
        is_due_for_review = (models.Article.last_read_date.is_not(None)) & (
            models.Article.last_read_date + timedelta(days=float(models.Article.review_days)) <= datetime.now()
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


@router.post('/', response_model=schemas.Article, status_code=status.HTTP_201_CREATED)
async def create(obj_in: schemas.ArticleCreate, session: Session = Depends(get_sqlalchemy_session)):
    obj = models.Article(**obj_in.model_dump())
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
    logger.debug(f'searching for {q=}')
    search_terms = [f'%{term.strip()}%' for term in q.split(',')]
    logger.debug(f'search terms: {search_terms}')
    conditions = [cast((models.Article.tags), postgresql.TEXT).ilike(term) for term in search_terms]
    articles = select(models.Article).filter(or_(*conditions)).order_by(models.Article.title.asc())
    logger.debug(articles)
    results = session.scalars(articles).all()
    logger.debug(f'search found {len(results)} results')
    return list(results)


@dataclass
class ArticleSummary:
    title: str
    summary: str
    tags: list[str]


@router.post('/summarize/', response_model=ArticleSummary, status_code=status.HTTP_201_CREATED)
async def summarize(url: str = Body(media_type='text/plain')):
    """Summarize youtube video or article based on the url.

    Return a summary of the article or video including title, summary, tags. If youtube video, use captions for video
    summary. If article, use html content for summary. Using openai chat to summarize and provide tags.
    """

    def _get_youtube_video_text_captions(url: str) -> str:
        yt_trans = YouTubeTranscriptApi()
        formatter = TextFormatter()
        video_id = url.split('v=')[1]
        transcript = yt_trans.get_transcript(video_id)
        formatted = formatter.format_transcript(transcript)
        return formatted

    def _get_formatted_title(soup: BeautifulSoup) -> str:
        if soup.title and soup.title.string:
            title = soup.title.string.split('|')[0].replace('...', '')
        else:
            title = 'Could not parse title'
        return title

    def _get_text_content_from_html(soup: BeautifulSoup) -> str:
        relevant_content_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'li']
        tag_content = soup.find_all(relevant_content_tags)
        text_content = ' '.join(tag.get_text() for tag in tag_content)
        return text_content

    def _get_summary_and_tags_from_openai(text_content: str):
        client = OpenAI(api_key=settings.openai.api_key)
        assistant = client.beta.assistants.create(
            name='Content Summarizer with Tags',
            instructions=settings.openai.articles_summary_instructions,
            model=settings.openai.model,
        )
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role='user',
            content=f'Create a summary and tags from the following content: \n{text_content}',
        )
        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
        while run.status in ('queued', 'in_progress'):
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id,
            )
            time.sleep(1)
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        data = json.loads(messages.data[0].content[0].text.value)  # type: ignore
        logger.info(f'tokens used: {run.usage.total_tokens}')  # type: ignore
        logger.debug(f'openai summary returned: {data}')
        summary = data.get('summary')
        tags = data.get('tags')
        return summary, tags

    logger.debug(f'summarizing url: {url}')
    url_response = httpx.get(url, follow_redirects=True).raise_for_status()
    soup = BeautifulSoup(url_response.content, 'html.parser')

    if "youtube.com" in url or "youtu.be" in url:
        text_content = _get_youtube_video_text_captions(url)
    else:
        text_content = _get_text_content_from_html(soup)

    title = _get_formatted_title(soup)
    summary, tags = _get_summary_and_tags_from_openai(text_content)
    return ArticleSummary(title, summary, tags)


@router.get('/{id}/', response_model=schemas.Article, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if event := session.get(models.Article, id):
        return event
    else:
        IDNotFoundError(id)


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if event := session.get(models.Article, id):
        session.delete(event)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        IDNotFoundError(id)


@router.patch('/{id}/', response_model=schemas.Article, status_code=status.HTTP_200_OK)
async def complete(id: int, update: schemas.ArticleUpdate, session: Session = Depends(get_sqlalchemy_session)):
    logger.debug(f'INPUT DATA: {update}')
    if obj := session.get(models.Article, id):
        update_data = update.model_dump(exclude_unset=True)
        for attr, value in update_data.items():
            setattr(obj, attr, value)
        logger.debug(f'UPDATED: {obj}')
        session.commit()
        session.refresh(obj)
        logger.debug(f'RETURNING: {obj}')
        return obj
    else:
        IDNotFoundError(id)
