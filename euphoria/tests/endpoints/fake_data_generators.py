import random


class FakeTaskDataGenerator:
    """Generate fake task data
    """

    def __init__(self, endpoint, seed):
        self.endpoint = endpoint
        self.seed = seed
        self.generated_data = None

        if self.seed:
            random.seed(seed)

    def generate(self, num_records: int) -> list[dict]:
        self.generated_data = [
            {
                "name": f"task-{num:03}",
                "category": f"category-{num:03}",
                "priority": random.randint(1, 100),
            }
            for num in range(num_records)
        ]
        return self.generated_data

    def ids_from_generated(self, num_records: int) -> list[int]:
        if not self.generated_data:
            return AttributeError('No data has been generated')
        return random.choices(range(0, len(self.generated_data) - 1), k=num_records)

    def records_from_generated(self, num_records: int) -> list[dict]:
        if not self.generated_data:
            return AttributeError('No data has been generated')
        return random.choices(self.generated_data, k=num_records)
