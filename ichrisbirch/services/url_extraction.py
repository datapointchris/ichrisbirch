"""Turn a saved URL into the title and text a summary is written from.

Consumers: `api/endpoints/articles.py` (create, summarize, insights and the bulk
import worker) and `services/url_ingest.py` (recipe import).

`read_article_page` is the entry point. It refuses a page that is not the
article: one the site redirected to its homepage or a section index, a bot
challenge standing in for the page, or a page with too little text to be about
anything. Each refusal is its own exception, so the import worker records why
and a caller can branch on which.
"""

import io
import re
from dataclasses import dataclass
from urllib.parse import unquote
from urllib.parse import urlsplit

import structlog
import trafilatura
import yt_dlp
from bs4 import BeautifulSoup
from bs4 import Tag
from pypdf import PdfReader
from pypdf.errors import PyPdfError
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from ichrisbirch.services.outbound_http import get_page

logger = structlog.get_logger()

# Below this, what extraction found is not writing: a cookie notice, a login
# prompt, a post whose content is an image, a JavaScript app shell. A summary
# of any of those describes the page chrome and reads as if it were the article.
MIN_READABLE_WORDS = 40

# Titles a site serves in place of the page when it has decided the request is a
# bot. Each separator-delimited segment of the document <title> is compared
# lowercased and exact — Reddit's is "Reddit - Prove your humanity", where the
# phrase is the part a suffix strip would discard — so an article merely
# mentioning one of the phrases is not caught.
BOT_CHALLENGE_TITLES = frozenset(
    {
        'just a moment...',  # Cloudflare's interstitial
        'attention required!',  # Cloudflare's block page
        'prove your humanity',  # Reddit
        'access denied',  # Akamai, served by Stanford Online among others
    }
)

TITLE_SUFFIX_SEPARATORS = (' | ', ' - ', ' — ', ' · ')


class PageUnreadable(Exception):
    """The site answered, but what it sent is not the page that was saved."""

    def __init__(self, url: str, message: str):
        super().__init__(message)
        self.url = url


class PageRedirectedAway(PageUnreadable):
    """The site redirected the page to its homepage or to a section above it."""

    def __init__(self, url: str, final_url: str):
        super().__init__(url, f'{url} now redirects to {final_url}, not to the page that was saved')
        self.final_url = final_url


class PageIsBotChallenge(PageUnreadable):
    """The site served a bot check in place of the page."""

    def __init__(self, url: str, title: str):
        super().__init__(url, f'{url} served a bot check ("{title}") in place of the page')
        self.title = title


class PageIsUnreadablePdf(PageUnreadable):
    """The link is a PDF that could not be parsed: damaged, encrypted or not really a PDF."""

    def __init__(self, url: str, reason: str):
        super().__init__(url, f'{url} is a PDF that could not be read: {reason}')
        self.reason = reason


class PageHasNoText(PageUnreadable):
    """Extraction found too little text to summarize."""

    def __init__(self, url: str, word_count: int):
        super().__init__(url, f'{url} has {word_count} words of readable text, below the {MIN_READABLE_WORDS} a summary needs')
        self.word_count = word_count


@dataclass(frozen=True)
class YouTubeMetadata:
    title: str | None
    description: str | None
    uploader: str | None
    duration_seconds: int | None


@dataclass(frozen=True)
class ArticlePage:
    """What a summary is written from. `url` is where the page was finally served."""

    url: str
    title: str
    text: str


def is_youtube_url(url: str) -> bool:
    return 'youtube.com' in url or 'youtu.be' in url


def extract_video_id(url: str) -> str:
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


def get_youtube_video_text_captions(url: str) -> str:
    video_id = extract_video_id(url)
    yt_trans = YouTubeTranscriptApi()
    formatter = TextFormatter()
    transcript = yt_trans.fetch(video_id)
    return formatter.format_transcript(transcript)


def get_youtube_video_metadata(url: str) -> YouTubeMetadata:
    """Fetch title/description/uploader/duration via yt-dlp without downloading the video.

    Returns a YouTubeMetadata with all-None fields if the fetch fails — yt-dlp breaks
    regularly as YouTube changes, so a failure is non-fatal. Callers should fall
    through to transcript-only extraction on empty metadata.
    """
    try:
        with yt_dlp.YoutubeDL({'skip_download': True, 'quiet': True, 'no_warnings': True}) as ydl:
            info = ydl.extract_info(url, download=False) or {}
    except Exception as e:
        logger.warning('yt_dlp_metadata_fetch_failed', url=url, error=str(e))
        return YouTubeMetadata(title=None, description=None, uploader=None, duration_seconds=None)

    duration = info.get('duration')
    return YouTubeMetadata(
        title=info.get('title'),
        description=info.get('description'),
        uploader=info.get('uploader') or info.get('channel'),
        duration_seconds=int(duration) if isinstance(duration, int | float) else None,
    )


def strip_site_suffix(title: str) -> str:
    """Drop a trailing site name: "Article Title | Site Name" becomes "Article Title".

    Splits on the last separator, and only when what follows is four words or
    fewer, so a title using a separator inside itself survives.
    """
    for separator in TITLE_SUFFIX_SEPARATORS:
        if separator in title:
            head, tail = title.rsplit(separator, 1)
            if len(tail.split()) <= 4:
                title = head
            break
    return title.removesuffix(' - YouTube').strip()


def get_page_title(soup: BeautifulSoup) -> str | None:
    """The page's own title: og:title, then the document <title>, then the first <h1>.

    The document <title> is read from <head> only. An inline SVG carries its own
    <title> for accessibility, and a site that draws its logo that way puts
    "Site Logo" first in the document.
    """
    og_title = soup.find('meta', attrs={'property': 'og:title'})
    head_title = soup.head.find('title') if isinstance(soup.head, Tag) else None
    first_heading = soup.find('h1')
    candidates = (
        og_title.get('content') if isinstance(og_title, Tag) else None,
        head_title.get_text() if isinstance(head_title, Tag) else None,
        first_heading.get_text() if isinstance(first_heading, Tag) else None,
    )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return strip_site_suffix(' '.join(candidate.split()))
    return None


def bot_challenge_title(soup: BeautifulSoup) -> str | None:
    """The document <title> when it is a bot check standing in for the page, else None."""
    head_title = soup.head.find('title') if isinstance(soup.head, Tag) else None
    if not isinstance(head_title, Tag):
        return None
    title = ' '.join(head_title.get_text().split())
    segments = re.split('|'.join(re.escape(separator) for separator in TITLE_SUFFIX_SEPARATORS), title)
    if any(segment.strip().lower() in BOT_CHALLENGE_TITLES for segment in segments):
        return title
    return None


def extract_main_text(content: bytes, url: str) -> str:
    """The page's main text, without navigation, share rows, sidebars or related-post cards.

    Recall is favored, because a summary written from a little too much text is
    still about the article and one written from too little is not. Tables are
    kept for recipes and reference pages; a site's own comment section is not
    the article and is left out.
    """
    text = trafilatura.extract(content, url=url, favor_recall=True, include_tables=True, include_comments=False)
    return text or ''


def is_pdf(content: bytes) -> bool:
    """Whether a response body is a PDF, by its signature rather than a content type servers often get wrong."""
    return content.startswith(b'%PDF-')


def title_from_file_name(url: str) -> str | None:
    """A title made from the last path segment: `A_Good_Tech_Resume.pdf` becomes "A Good Tech Resume"."""
    name = unquote(urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1])
    stem = re.sub(r'\.pdf$', '', name, flags=re.IGNORECASE)
    words = re.sub(r'[_\-]+', ' ', stem).split()
    return ' '.join(words) or None


def read_pdf(content: bytes, url: str) -> tuple[str | None, str]:
    """A PDF's title and its text, one paragraph per page.

    Whitespace inside a page is collapsed, because text laid out in a PDF often
    extracts one word per line and the line breaks carry nothing.
    """
    try:
        reader = PdfReader(io.BytesIO(content))
        pages = [' '.join((page.extract_text() or '').split()) for page in reader.pages]
        metadata_title = reader.metadata.title if reader.metadata is not None else None
    except PyPdfError as e:
        raise PageIsUnreadablePdf(url, str(e)) from e
    title = metadata_title.strip() if isinstance(metadata_title, str) and metadata_title.strip() else title_from_file_name(url)
    return title, '\n\n'.join(page for page in pages if page)


def redirected_away(requested_url: str, final_url: str) -> bool:
    """Whether a redirect replaced the page with the site's homepage or a section above it.

    A moved article lands on another path and is still the article. Landing on
    `/`, or on a path the requested one sits under, is the site saying the page
    is gone and sending the reader somewhere general instead.
    """
    requested_path = urlsplit(requested_url).path.rstrip('/')
    final_path = urlsplit(final_url).path.rstrip('/')
    if not requested_path or final_path == requested_path:
        return False
    return final_path == '' or requested_path.startswith(final_path + '/')


def read_article_page(url: str) -> ArticlePage:
    """Fetch a saved page and return its title and the text to summarize.

    A YouTube video's text is its captions and a PDF's is its pages. Everything
    else is extracted from the page, after refusing a redirect away from it and a
    bot check in its place. Every kind is refused when it has too little text.
    """
    page = get_page(url).raise_for_status()
    if redirected_away(page.requested_url, page.url):
        raise PageRedirectedAway(url, page.url)

    if is_pdf(page.content):
        title, text = read_pdf(page.content, page.url)
    else:
        soup = BeautifulSoup(page.content, 'html.parser')
        if (challenge := bot_challenge_title(soup)) is not None:
            raise PageIsBotChallenge(url, challenge)
        title = get_page_title(soup)
        text = get_youtube_video_text_captions(url) if is_youtube_url(url) else extract_main_text(page.content, page.url)

    word_count = len(text.split())
    if word_count < MIN_READABLE_WORDS:
        raise PageHasNoText(url, word_count)
    return ArticlePage(url=page.url, title=title or page.url, text=text)
