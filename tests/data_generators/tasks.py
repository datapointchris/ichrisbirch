import random
from typing import Optional

from faker import Faker

from ichrisbirch.models.task import TaskCategory

from .base import FakeDataGenerator


class TaskDataGenerator(FakeDataGenerator):
    """Fake task data generator"""

    def __init__(self, total_records: int, num_test_records: int, seed: Optional[int] = None):
        self.total_records = total_records
        self.num_test_records = num_test_records
        self.seed = seed
        self.fake = Faker()

        if self.seed:
            random.seed(seed)
            Faker.seed(seed)

    def generate(self) -> list[dict]:
        """Generate fake task data"""
        return [
            {
                'name': self.fake.catch_phrase(),
                'notes': self.fake.sentence(),
                'category': random.choice([task.value for task in TaskCategory]),
                'priority': random.randint(1, 100),  # TODO: Is this taking seed?
            }
            for num in range(self.total_records)
        ]
