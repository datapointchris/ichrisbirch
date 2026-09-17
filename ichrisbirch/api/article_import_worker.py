"""Background worker for bulk article imports via Redis queue.

Queue item format (JSON string in Redis list):
    {"batch_id": "...", "url": "...", "notes": "...", "attempt": 1}

Batch status (Redis hash at article_import:batch:{batch_id}):
    status, total, processed, succeeded, failed_count, errors (JSON), results (JSON),
    created_at, updated_at

Pause (Redis string at article_import:paused_until):
    the ISO time the Claude usage limit resets, expiring at that time. While it
    exists no worker takes an item, and every unfinished batch reads as paused.
"""

import asyncio
import json
import math
import threading
import uuid
from datetime import UTC
from datetime import datetime
from datetime import timedelta

import pendulum
import redis
import structlog

from ichrisbirch import models
from ichrisbirch.ai.assistants.anthropic import AssistantUsageLimitReached
from ichrisbirch.config import Settings
from ichrisbirch.database.session import create_session
from ichrisbirch.services.outbound_http import PageStatusError
from ichrisbirch.services.url_extraction import CaptionsBlocked
from ichrisbirch.services.url_extraction import PageUnreadable
from ichrisbirch.util import clean_url

logger = structlog.get_logger()

QUEUE_KEY = 'article_import:queue'
BATCH_KEY_PREFIX = 'article_import:batch:'
PAUSE_KEY = 'article_import:paused_until'
BATCH_TTL = 86400  # 24 hours
MAX_ATTEMPTS = 2
# How long to hold the queue when the usage limit gives no reset time.
USAGE_LIMIT_RECHECK = timedelta(minutes=15)


def _worth_retrying(error: Exception) -> bool:
    """Whether asking again at once could give a different answer.

    A page that is not the article, a duplicate and a 4xx stay the same on a
    second request. A site refusing because of how many requests it has had gets
    a second one, which is what keeps the refusal going. A dropped connection or a
    5xx can pass, so those are retried.
    """
    from ichrisbirch.api.endpoints.articles import ArticleAlreadyExists

    if isinstance(error, PageUnreadable | CaptionsBlocked | ArticleAlreadyExists):
        return False
    return not (isinstance(error, PageStatusError) and error.status_code < 500)


def enqueue_bulk_import(redis_client: redis.Redis, urls: list[str], notes_map: dict[str, str] | None = None) -> str:
    """Enqueue URLs for bulk import. Returns batch_id."""
    batch_id = str(uuid.uuid4())
    notes_map = notes_map or {}

    pipeline = redis_client.pipeline()
    for url in urls:
        item = json.dumps(
            {
                'batch_id': batch_id,
                'url': clean_url(url.strip()),
                'notes': notes_map.get(url),
                'attempt': 1,
            }
        )
        pipeline.rpush(QUEUE_KEY, item)

    batch_key = f'{BATCH_KEY_PREFIX}{batch_id}'
    now = datetime.now(UTC).isoformat()
    pipeline.hset(
        batch_key,
        mapping={
            'status': 'queued',
            'total': len(urls),
            'processed': 0,
            'succeeded': 0,
            'failed_count': 0,
            'errors': '[]',
            'results': '[]',
            'created_at': now,
            'updated_at': now,
        },
    )
    pipeline.expire(batch_key, BATCH_TTL)
    pipeline.execute()

    logger.info('bulk_import_enqueued', batch_id=batch_id, count=len(urls))
    return batch_id


def get_batch_status(redis_client: redis.Redis, batch_id: str) -> dict | None:
    """Get status of a bulk import batch."""
    batch_key = f'{BATCH_KEY_PREFIX}{batch_id}'
    data = redis_client.hgetall(batch_key)
    if not data:
        return None
    paused_until = redis_client.get(PAUSE_KEY)
    paused = paused_until is not None and data['status'] != 'completed'
    return {
        'batch_id': batch_id,
        'status': 'paused' if paused else data['status'],
        'resumes_at': paused_until if paused else None,
        'total': int(data['total']),
        'processed': int(data['processed']),
        'succeeded': int(data['succeeded']),
        'failed_count': int(data['failed_count']),
        'errors': json.loads(data['errors']),
        'results': json.loads(data['results']),
        'created_at': data['created_at'],
        'updated_at': data['updated_at'],
    }


class ArticleImportWorker:
    """Daemon thread that processes article import queue via BLPOP."""

    def __init__(self, redis_client: redis.Redis, settings: Settings):
        self.redis_client = redis_client
        self.settings = settings
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True, name='article-import-worker')
        self._thread.start()
        logger.info('article_import_worker_started')

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10)
        logger.info('article_import_worker_stopped')

    def _run(self):
        while not self._stop_event.is_set():
            try:
                if (pause_seconds := self.redis_client.ttl(PAUSE_KEY)) > 0:
                    self._stop_event.wait(timeout=pause_seconds)
                    continue
                result = self.redis_client.blpop(QUEUE_KEY, timeout=5)
                if result is None:
                    continue
                _, item_json = result
                item = json.loads(item_json)
                self._process_item(item)
            except Exception:
                logger.exception('article_import_worker_error')
                if self._stop_event.wait(timeout=2):
                    break

    def _process_item(self, item: dict):
        batch_id = item['batch_id']
        url = item['url']
        attempt = item.get('attempt', 1)
        notes = item.get('notes')
        batch_key = f'{BATCH_KEY_PREFIX}{batch_id}'

        # Mark batch as processing
        self.redis_client.hset(batch_key, 'status', 'processing')
        self.redis_client.hset(batch_key, 'updated_at', datetime.now(UTC).isoformat())

        try:
            with create_session(self.settings) as session:
                from ichrisbirch.api.endpoints.articles import _summarize_and_create_article

                article = asyncio.run(_summarize_and_create_article(url, notes, session, self.settings))
                self._record_success(batch_key, url, article.title)
        except AssistantUsageLimitReached as e:
            self._hold_for_usage_limit(item, e)
        except Exception as e:
            error_msg = str(e)
            logger.warning('article_import_item_failed', url=url, attempt=attempt, error=error_msg)

            if attempt < MAX_ATTEMPTS and _worth_retrying(e):
                # Re-queue with incremented attempt
                retry_item = json.dumps(
                    {
                        'batch_id': batch_id,
                        'url': url,
                        'notes': notes,
                        'attempt': attempt + 1,
                    }
                )
                self.redis_client.rpush(QUEUE_KEY, retry_item)
            else:
                # Permanent failure — write to DB
                self._record_permanent_failure(batch_key, url, error_msg, batch_id)

    def _hold_for_usage_limit(self, item: dict, limit: AssistantUsageLimitReached):
        """Put the item back at the head of the queue and pause the queue until the limit resets.

        The item keeps its attempt count, because the limit refused the call rather
        than the page or the reply failing. The pause lives in Redis and expires at
        the reset, so a worker that restarts meanwhile holds too. Every batch with an
        item still queued keeps its status for a day past the reset, so a weekly
        limit does not expire the batches it is holding up.
        """
        now = datetime.now(UTC)
        resumes_at = limit.resets_at if limit.resets_at is not None and limit.resets_at > now else now + USAGE_LIMIT_RECHECK
        pause_seconds = math.ceil((resumes_at - now).total_seconds())
        waiting_batch_ids = {json.loads(queued)['batch_id'] for queued in self.redis_client.lrange(QUEUE_KEY, 0, -1)}
        waiting_batch_ids.add(item['batch_id'])

        pipeline = self.redis_client.pipeline()
        pipeline.lpush(QUEUE_KEY, json.dumps(item))
        pipeline.set(PAUSE_KEY, resumes_at.isoformat(), ex=pause_seconds)
        for batch_id in waiting_batch_ids:
            pipeline.expire(f'{BATCH_KEY_PREFIX}{batch_id}', pause_seconds + BATCH_TTL, gt=True)
        pipeline.execute()
        logger.warning('article_import_paused', url=item['url'], resumes_at=resumes_at.isoformat(), limit_type=limit.limit_type)

    def _record_success(self, batch_key: str, url: str, title: str):
        pipeline = self.redis_client.pipeline()
        pipeline.hincrby(batch_key, 'processed', 1)
        pipeline.hincrby(batch_key, 'succeeded', 1)
        pipeline.hset(batch_key, 'updated_at', datetime.now(UTC).isoformat())
        pipeline.execute()

        # Append to results list
        results = json.loads(self.redis_client.hget(batch_key, 'results') or '[]')
        results.append({'url': url, 'title': title})
        self.redis_client.hset(batch_key, 'results', json.dumps(results))

        self._check_batch_complete(batch_key)

    def _record_permanent_failure(self, batch_key: str, url: str, error_msg: str, batch_id: str):
        pipeline = self.redis_client.pipeline()
        pipeline.hincrby(batch_key, 'processed', 1)
        pipeline.hincrby(batch_key, 'failed_count', 1)
        pipeline.hset(batch_key, 'updated_at', datetime.now(UTC).isoformat())
        pipeline.execute()

        # Append to errors list
        errors = json.loads(self.redis_client.hget(batch_key, 'errors') or '[]')
        errors.append({'url': url, 'error': error_msg})
        self.redis_client.hset(batch_key, 'errors', json.dumps(errors))

        # Write to persistent failed_article_imports table
        try:
            with create_session(self.settings) as session:
                failed = models.ArticleFailedImport(
                    url=url,
                    batch_id=batch_id,
                    error_message=error_msg,
                    failed_at=pendulum.now(),
                )
                session.add(failed)
                session.commit()
        except Exception:
            logger.exception('failed_article_import_db_write_error', url=url)

        self._check_batch_complete(batch_key)

    def _check_batch_complete(self, batch_key: str):
        data = self.redis_client.hgetall(batch_key)
        if int(data.get('processed', 0)) >= int(data.get('total', 0)):
            self.redis_client.hset(batch_key, 'status', 'completed')
            self.redis_client.hset(batch_key, 'updated_at', datetime.now(UTC).isoformat())
            logger.info('bulk_import_batch_completed', batch_key=batch_key)
