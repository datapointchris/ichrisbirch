import random

from .base import FakeDataGenerator
from ichrisbirch.models.tasks import TaskCategory


class TaskDataGenerator(FakeDataGenerator):
    """Fake Task Data"""

    def __init__(self, seed):
        super().__init__(seed)

    def generate(self, num_records: int) -> list[dict]:
        self.generated_data = [
            {
                'name': self.fake.catch_phrase(),
                'notes': self.fake.sentence(),
                'category': random.choice([task.value for task in TaskCategory]),
                'priority': random.randint(1, 100),  # TODO: Is this taking seed?
            }
            for num in range(num_records)
        ]
