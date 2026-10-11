"""Save an article from its URL: read the page, summarize and tag it, persist it.

Used by `POST /articles/create-from-url/` and the bulk import worker, which the
endpoint module also enqueues into. Both import this module, so neither has to
import the other.
"""

import pendulum
import structlog
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.ai.assistants.anthropic import AnthropicAssistant
from ichrisbirch.config import Settings
from ichrisbirch.services.url_extraction import read_article_page
from ichrisbirch.util import clean_url

logger = structlog.get_logger()


class ArticleAlreadyExists(Exception):
    """An article with this URL is already saved."""

    def __init__(self, url: str):
        super().__init__(f'Article already exists: {url}')
        self.url = url


async def summarize_and_create_article(url: str, notes: str | None, session: Session, settings: Settings) -> models.Article:
    """Fetch URL, summarize via Claude, create article.

    It raises domain exceptions and each caller decides what one means: the
    endpoint answers a status, the worker records the message.
    """
    url = clean_url(url)
    existing = session.scalar(select(models.Article).where(models.Article.url == url))
    if existing:
        raise ArticleAlreadyExists(url)

    page = await run_in_threadpool(read_article_page, url)

    assistant = AnthropicAssistant(
        name='Article Summary with Tags',
        system_prompt=settings.ai.prompts.article_summary_tags,
        settings=settings,
    )
    written = await assistant.generate_structured(page.text, schemas.ArticleSummaryAndTags, max_tokens=8192)

    article = models.Article(
        title=page.title,
        url=url,
        tags=written.tags,
        summary=written.summary,
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
    logger.info('article_created_from_url', url=url, title=page.title)
    return article
