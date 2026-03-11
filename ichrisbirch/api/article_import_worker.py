"""Background worker for bulk article imports via Redis queue.

Queue item format (JSON string in Redis list):
    {"batch_id": "...", "url": "...", "notes": "...", "attempt": 1}

Batch status (Redis hash at article_import:batch:{batch_id}):
    status, total, processed, succeeded, failed_count, errors (JSON), results (JSON),
    created_at, updated_at
"""

import json
import threading
import uuid
from datetime import datetime

import pendulum
import redis
import structlog

from ichrisbirch import models
from ichrisbirch.config import Settings
from ichrisbirch.database.session import create_session

logger = structlog.get_logger()

QUEUE_KEY = 'article_import:queue'
BATCH_KEY_PREFIX = 'article_import:batch:'
BATCH_TTL = 86400  # 24 hours
MAX_ATTEMPTS = 2


def enqueue_bulk_import(redis_client: redis.Redis, urls: list[str], notes_map: dict[str, str] | None = None) -> str:
    """Enqueue URLs for bulk import. Returns batch_id."""
    batch_id = str(uuid.uuid4())
    notes_map = notes_map or {}

    pipeline = redis_client.pipeline()
    for url in urls:
        item = json.dumps(
            {
                'batch_id': batch_id,
                'url': url.strip(),
                'notes': notes_map.get(url),
                'attempt': 1,
            }
        )
        pipeline.rpush(QUEUE_KEY, item)

    batch_key = f'{BATCH_KEY_PREFIX}{batch_id}'
    now = datetime.now().isoformat()
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
    return {
        'batch_id': batch_id,
        'status': data['status'],
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
        self.redis_client.hset(batch_key, 'updated_at', datetime.now().isoformat())

        try:
            with create_session(self.settings) as session:
                from ichrisbirch.api.endpoints.articles import _summarize_and_create_article

                article = _summarize_and_create_article(url, notes, session, self.settings)
                self._record_success(batch_key, url, article.title)
        except Exception as e:
            error_msg = str(e)
            logger.warning('article_import_item_failed', url=url, attempt=attempt, error=error_msg)

            if attempt < MAX_ATTEMPTS:
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

    def _record_success(self, batch_key: str, url: str, title: str):
        pipeline = self.redis_client.pipeline()
        pipeline.hincrby(batch_key, 'processed', 1)
        pipeline.hincrby(batch_key, 'succeeded', 1)
        pipeline.hset(batch_key, 'updated_at', datetime.now().isoformat())
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
        pipeline.hset(batch_key, 'updated_at', datetime.now().isoformat())
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
            self.redis_client.hset(batch_key, 'updated_at', datetime.now().isoformat())
            logger.info('bulk_import_batch_completed', batch_key=batch_key)
