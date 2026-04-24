"""URL → classifier pipeline for the recipes/techniques import flow.

Used by `POST /recipes/import-from-url/`. Orchestrates content extraction
(YouTube description + transcript, or article HTML text) and passes the
labeled content to a Claude classifier that returns a UrlImportCandidate.
"""

import httpx
import structlog
from bs4 import BeautifulSoup
from pydantic import ValidationError

from ichrisbirch import schemas
from ichrisbirch.ai.assistants.anthropic import AnthropicAssistant
from ichrisbirch.config import Settings
from ichrisbirch.services.url_extraction import get_text_content_from_html
from ichrisbirch.services.url_extraction import get_youtube_video_metadata
from ichrisbirch.services.url_extraction import get_youtube_video_text_captions

logger = structlog.get_logger()


class ClassifierOutputError(Exception):
    """Raised when the classifier's output fails to validate.

    Carries the raw classifier output so the endpoint can embed it in the 502
    response — gives observability into prompt drift without a separate log dive.
    """

    def __init__(self, message: str, raw_output: str):
        super().__init__(message)
        self.raw_output = raw_output


def is_youtube_url(url: str) -> bool:
    return 'youtube.com' in url or 'youtu.be' in url


def extract_content_for_classifier(url: str, settings: Settings) -> str:
    """Build the labeled content block the classifier reads.

    YouTube: description + transcript, each in its own labeled section so Claude
    can weigh the canonical written recipe (description) against the spoken
    context (transcript). If either fetch fails, the other section is still used.

    Articles: plain text extracted via bs4, noise stripped.
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

    response = httpx.get(url, follow_redirects=True, headers=settings.mac_safari_request_headers, timeout=30.0)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    return get_text_content_from_html(soup)


def classify_url_content(url: str, hint: str, content: str, settings: Settings) -> schemas.UrlImportCandidate:
    """Run the classifier and parse its output into a UrlImportCandidate.

    Raises `ClassifierOutputError` with the raw output preserved when the
    classifier returns malformed or invalid JSON. The endpoint layer translates
    that to HTTP 502.
    """
    assistant = AnthropicAssistant(
        name='URL Import Classifier',
        system_prompt=settings.ai.prompts.url_import_classifier,
        settings=settings,
    )
    user_message = f'url: {url}\nhint: {hint}\n\n{content}'
    raw_output = assistant.generate(user_message, max_tokens=8192)

    try:
        parsed = AnthropicAssistant.parse_json(raw_output)
    except Exception as e:
        raise ClassifierOutputError(f'Classifier returned non-JSON output: {e}', raw_output) from e

    if not isinstance(parsed, dict):
        raise ClassifierOutputError('Classifier returned a non-object top-level value', raw_output)

    try:
        candidate = schemas.UrlImportCandidate.model_validate(parsed)
    except ValidationError as e:
        raise ClassifierOutputError(f'Candidate did not validate: {e}', raw_output) from e

    # Always pin source_url to the input URL — the classifier sometimes drops or
    # rewrites it, but the endpoint needs it for the duplicate check on re-ingest.
    if candidate.recipe is not None and candidate.recipe.source_url != url:
        candidate.recipe = candidate.recipe.model_copy(update={'source_url': url})
    if candidate.technique is not None and candidate.technique.source_url != url:
        candidate.technique = candidate.technique.model_copy(update={'source_url': url})

    return candidate
