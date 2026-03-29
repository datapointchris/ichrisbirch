"""Seed articles with varied read states and tags."""

from __future__ import annotations

import random
from datetime import UTC
from datetime import datetime
from datetime import timedelta

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.article import Article
from scripts.seed.base import SeedResult

ARTICLES = [
    ('Understanding Python Asyncio', 'https://example.com/python-asyncio', ['python', 'async', 'concurrency']),
    ('PostgreSQL Performance Tuning', 'https://example.com/pg-perf', ['databases', 'postgresql', 'performance']),
    ('The Twelve-Factor App', 'https://example.com/12factor', ['architecture', 'devops', 'best-practices']),
    ('Kubernetes Best Practices', 'https://example.com/k8s-bp', ['kubernetes', 'devops', 'containers']),
    ('SQLAlchemy 2.0 Migration Guide', 'https://example.com/sqla2', ['python', 'databases', 'sqlalchemy']),
    ('Git Internals - How Git Works', 'https://example.com/git-int', ['git', 'internals', 'devops']),
    ('Docker Networking Deep Dive', 'https://example.com/docker-net', ['docker', 'networking', 'devops']),
    ('FastAPI vs Flask: A Comparison', 'https://example.com/fastapi-flask', ['python', 'web-frameworks']),
    ('Redis Caching Strategies', 'https://example.com/redis-cache', ['redis', 'caching', 'performance']),
    ('Terraform Best Practices', 'https://example.com/terraform-bp', ['terraform', 'infrastructure', 'devops']),
]

SUMMARIES = [
    'A comprehensive guide to asynchronous programming patterns in modern Python.',
    'Practical techniques for optimizing PostgreSQL query performance and indexing.',
    'Methodology for building modern, scalable, maintainable web applications.',
    'Production-tested patterns for running workloads on Kubernetes clusters.',
    'Step-by-step migration guide from SQLAlchemy 1.x to 2.0 style.',
    "Deep dive into Git's object model, packfiles, and reference management.",
    'Understanding bridge, overlay, and host networking in Docker environments.',
    'Feature comparison between FastAPI and Flask for Python web development.',
    'Strategies for effective caching with Redis including TTL and eviction.',
    'Infrastructure as code patterns and organizational best practices.',
]


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM articles'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    articles = []
    current_count = 0

    for rep in range(scale):
        for i, (title, url, tags) in enumerate(ARTICLES):
            article_title = title if scale == 1 else f'{title} #{rep + 1}'
            article_url = url if scale == 1 else f'{url}-{rep + 1}'
            save_date = datetime.now(UTC) - timedelta(days=random.randint(1, 365))

            is_current = i == 0
            is_archived = i >= 7
            is_favorite = i in (0, 2, 4)
            read_count = random.randint(0, 5) if not is_current else 0
            last_read = save_date + timedelta(days=random.randint(1, 30)) if read_count > 0 else None
            notes = f'Good reference for {tags[0]}' if i % 3 == 0 else None

            if is_current:
                current_count += 1

            articles.append(
                Article(
                    title=article_title,
                    url=article_url,
                    tags=tags,
                    summary=SUMMARIES[i],
                    save_date=save_date,
                    last_read_date=last_read,
                    read_count=read_count,
                    is_favorite=is_favorite,
                    is_current=is_current,
                    is_archived=is_archived,
                    notes=notes,
                )
            )

    session.add_all(articles)
    session.flush()

    archived = sum(1 for a in articles if a.is_archived)
    favorites = sum(1 for a in articles if a.is_favorite)
    return SeedResult(
        model='Article',
        count=len(articles),
        details=f'{current_count} current, {archived} archived, {favorites} favorites',
    )
