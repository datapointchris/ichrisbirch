"""Shared helpers for extracting text content from URLs.

Consumers: `api/endpoints/articles.py`, `api/endpoints/recipes.py` (URL ingest).
"""

import re
from dataclasses import dataclass

import structlog
import yt_dlp
from bs4 import BeautifulSoup
from bs4 import Tag
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

logger = structlog.get_logger()


@dataclass(frozen=True)
class YouTubeMetadata:
    title: str | None
    description: str | None
    uploader: str | None
    duration_seconds: int | None


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


def strip_noise_tags(soup: BeautifulSoup) -> None:
    """Remove tags that contribute noise rather than content."""
    for tag_name in ('script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript', 'svg', 'form'):
        for tag in soup.find_all(tag_name):
            tag.decompose()
    noise_pattern = re.compile(r'comment|cookie|banner|popup|modal|sidebar|social|share|newsletter|advert', re.IGNORECASE)
    for attr in ('class', 'id'):
        for tag in soup.find_all(attrs={attr: noise_pattern}):
            if isinstance(tag, Tag):
                tag.decompose()


def get_text_content_from_html(soup: BeautifulSoup) -> str:
    """Extract readable text from HTML, preserving paragraph structure.

    Tries <article> tag first (standard semantic container for main content),
    then falls back to <main>, then the full <body>. Strips noise tags before
    extraction to avoid navigation menus, footers, cookie banners, etc.
    """
    strip_noise_tags(soup)

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
