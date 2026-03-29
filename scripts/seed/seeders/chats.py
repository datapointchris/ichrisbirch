"""Seed chat conversations with alternating user/assistant messages."""

from __future__ import annotations

import random

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.chat import Chat
from ichrisbirch.models.chatmessage import ChatMessage
from scripts.seed.base import SeedResult

# (name, category, subcategory)
CHATS = [
    ('Python asyncio help', 'programming', 'python'),
    ('Recipe ideas for meal prep', 'cooking', None),
    ('Home network setup', 'technology', 'networking'),
    ('Book recommendations 2025', 'reading', None),
    ('Travel planning Japan', 'travel', 'asia'),
]

USER_MESSAGES = [
    'Can you help me understand how async/await works in Python?',
    "What's the best way to structure a FastAPI application?",
    "I'm getting a weird error with SQLAlchemy sessions",
    'How do I set up a reverse proxy with Traefik?',
    'What books would you recommend for distributed systems?',
    'Can you explain the difference between threads and coroutines?',
    'I need help planning meals for the week',
    "What's the best router for a home lab setup?",
]

ASSISTANT_MESSAGES = [
    "Async/await in Python is built on coroutines. When you use `await`, you're yielding control back to the event loop.",
    'A common pattern is to organize by feature: routers, services, and schemas in separate modules.',
    "Session management in SQLAlchemy 2.0 uses context managers. Make sure you're not sharing sessions across threads.",
    'Traefik auto-discovers services via Docker labels. Set up entry points and routers in the static config.',
    "I'd recommend 'Designing Data-Intensive Applications' by Kleppmann as a great starting point.",
    'Threads use OS-level scheduling with preemptive multitasking, while coroutines use cooperative multitasking.',
    'For meal prep, start with 3-4 base proteins and rotating sides throughout the week.',
    'For a home lab, the Ubiquiti Dream Machine Pro handles routing, switching, and WiFi in one box.',
]


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM chat.messages'))
    session.execute(sqlalchemy.text('DELETE FROM chat.chats'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    chats = []
    message_count = 0

    for rep in range(scale):
        for i, (name, category, subcategory) in enumerate(CHATS):
            chat_name = name if scale == 1 else f'{name} #{rep + 1}'
            chat = Chat(
                name=chat_name,
                category=category,
                subcategory=subcategory,
                tags=[category] if category else None,
            )
            session.add(chat)
            session.flush()

            # 2-6 messages per chat (1-3 user/assistant pairs)
            num_pairs = random.randint(1, 3)
            for j in range(num_pairs):
                user_msg = USER_MESSAGES[(i + j) % len(USER_MESSAGES)]
                asst_msg = ASSISTANT_MESSAGES[(i + j) % len(ASSISTANT_MESSAGES)]
                session.add(ChatMessage(chat_id=chat.id, role='user', content=user_msg))
                session.add(ChatMessage(chat_id=chat.id, role='assistant', content=asst_msg))
                message_count += 2

            chats.append(chat)

    session.flush()

    return SeedResult(
        model='Chat',
        count=len(chats),
        details=f'{len(chats)} chats, {message_count} messages',
    )
