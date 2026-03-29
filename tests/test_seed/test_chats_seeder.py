"""Tests for the chats seeder."""

from __future__ import annotations

import pytest

from ichrisbirch.models.chat import Chat
from ichrisbirch.models.chatmessage import ChatMessage
from scripts.seed.seeders import chats

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestChatSeeder:
    def test_creates_chats(self, db):
        chats.clear(db)
        result = chats.seed(db, scale=1)
        assert result.count == len(chats.CHATS)

    def test_chats_have_messages(self, db):
        chats.clear(db)
        chats.seed(db, scale=1)
        for chat in db.query(Chat).all():
            msgs = db.query(ChatMessage).filter(ChatMessage.chat_id == chat.id).all()
            assert len(msgs) >= 2

    def test_messages_alternate_roles(self, db):
        chats.clear(db)
        chats.seed(db, scale=1)
        for chat in db.query(Chat).all():
            msgs = db.query(ChatMessage).filter(ChatMessage.chat_id == chat.id).order_by(ChatMessage.id).all()
            for i, msg in enumerate(msgs):
                expected_role = 'user' if i % 2 == 0 else 'assistant'
                assert msg.role == expected_role

    def test_scale_multiplier(self, db):
        chats.clear(db)
        r1 = chats.seed(db, scale=1)
        chats.clear(db)
        r2 = chats.seed(db, scale=2)
        assert r2.count > r1.count
