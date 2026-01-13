import time

import structlog
from openai import OpenAI

from ichrisbirch.config import Settings

logger = structlog.get_logger()


class OpenAIAssistant:
    def __init__(self, name: str, instructions: str, settings: Settings, response_format=None):
        self.name = name
        self.instructions = instructions
        self.settings = settings
        self.client = OpenAI(api_key=self.settings.ai.openai.api_key)
        self.assistant = self.client.beta.assistants.create(
            name=self.name,
            instructions=self.instructions,
            model=self.settings.ai.openai.model,
            response_format=response_format,
        )

    def generate(self, content: str) -> str:
        thread = self.client.beta.threads.create()
        self.client.beta.threads.messages.create(thread_id=thread.id, role='user', content=content)
        run = self.client.beta.threads.runs.create(thread_id=thread.id, assistant_id=self.assistant.id)
        while run.status in ('queued', 'in_progress'):
            run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            time.sleep(3)
        messages = self.client.beta.threads.messages.list(thread_id=thread.id)
        data = messages.data[0].content[0].text.value  # type: ignore
        logger.debug('openai_generated', data_preview=data[:100])
        tokens_used = run.usage.total_tokens  # type: ignore
        logger.info('openai_tokens_used', tokens=tokens_used)  # type: ignore
        return data
