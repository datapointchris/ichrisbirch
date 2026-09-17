"""URL → classifier pipeline for the recipes/techniques import flow.

Used by `POST /recipes/import-from-url/`. Orchestrates content extraction
(YouTube description + transcript, or article HTML text) and passes the
labeled content to a Claude classifier that returns a UrlImportCandidate.
"""

import structlog

from ichrisbirch import schemas
from ichrisbirch.ai.assistants.anthropic import AnthropicAssistant
from ichrisbirch.config import Settings
from ichrisbirch.services.url_extraction import get_youtube_video_metadata
from ichrisbirch.services.url_extraction import get_youtube_video_text_captions
from ichrisbirch.services.url_extraction import is_youtube_url
from ichrisbirch.services.url_extraction import read_article_page

logger = structlog.get_logger()


def extract_content_for_classifier(url: str) -> str:
    """Build the labeled content block the classifier reads.

    YouTube: description + transcript, each in its own labeled section so Claude
    can weigh the canonical written recipe (description) against the spoken
    context (transcript). If either fetch fails, the other section is still used.

    Articles: the page text `read_article_page` returns, which refuses a redirect
    away from the page, a bot check and a page with no readable text.
    """
    if is_youtube_url(url):
        metadata = get_youtube_video_metadata(url)
        try:
            transcript = get_youtube_video_text_captions(url)
        except Exception as e:
            logger.warning('youtube_transcript_fetch_failed', url=url, error=str(e))
            transcript = ''
        return (
            f'<title>{metadata.title or ""}</title>\n'
            f'<uploader>{metadata.uploader or ""}</uploader>\n'
            f'<description>{metadata.description or ""}</description>\n'
            f'<transcript>{transcript}</transcript>\n'
        )

    return read_article_page(url).text


async def classify_url_content(url: str, hint: str, content: str, settings: Settings) -> schemas.UrlImportCandidate:
    """Run the classifier and return its UrlImportCandidate.

    A classifier that produces no usable candidate raises the assistant's
    `AssistantOutputError`, carrying its reason and raw output, and the API's
    handler for that error answers HTTP 502.
    """
    assistant = AnthropicAssistant(
        name='URL Import Classifier',
        system_prompt=settings.ai.prompts.url_import_classifier,
        settings=settings,
    )
    user_message = f'url: {url}\nhint: {hint}\n\n{content}'
    candidate = await assistant.generate_structured(user_message, schemas.UrlImportCandidate, max_tokens=8192)

    # Always pin source_url to the input URL — the classifier sometimes drops or
    # rewrites it, but the endpoint needs it for the duplicate check on re-ingest.
    if candidate.recipe is not None and candidate.recipe.source_url != url:
        candidate.recipe = candidate.recipe.model_copy(update={'source_url': url})
    if candidate.technique is not None and candidate.technique.source_url != url:
        candidate.technique = candidate.technique.model_copy(update={'source_url': url})

    return candidate
