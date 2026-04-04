"""Tests for the chats seeder."""

from __future__ import annotations

import pytest

from ichrisbirch.models.chat import Chat
from ichrisbirch.models.chatmessage import ChatMessage
from scripts.seed.seeders import chats

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestChatSeeder:
    def test_chats_have_messages(self, db):
        chats.clear(db)
        chats.seed(db, scale=1)
        for chat in db.query(Chat).all():
            msgs = db.query(ChatMessage).filter(ChatMessage.chat_id == chat.id).all()
            assert len(msgs) >= 2
