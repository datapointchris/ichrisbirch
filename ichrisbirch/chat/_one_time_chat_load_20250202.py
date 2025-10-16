import json
import time

from ichrisbirch import models
from ichrisbirch.database.session import get_sqlalchemy_session

with open('chat_history.json') as f:
    chat_history = json.load(f)

session = next(get_sqlalchemy_session())

for chat in chat_history:
    messages = [models.ChatMessage(**message) for message in chat['messages']]
    chat = models.Chat(name=chat['name'], messages=messages)
    session.add(chat)
    session.commit()
    print(chat.name)
    time.sleep(0.1)
