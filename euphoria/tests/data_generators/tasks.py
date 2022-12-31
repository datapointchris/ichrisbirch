import random

from .base import FakeDataGenerator


class TaskDataGenerator(FakeDataGenerator):
    """Fake Task Data"""

    def __init__(self, seed):
        super().__init__(seed)

    def generate(self, num_records: int) -> list[dict]:
        self.generated_data = [
            {
                'name': self.fake.catch_phrase(),
                'notes': self.fake.sentence(),
                'category': random.choice(['financial', 'coding', 'chore', 'car', 'misc']),
                'priority': random.randint(1, 100),  # TODO: Is this taking seed?
            }
            for num in range(num_records)
        ]
