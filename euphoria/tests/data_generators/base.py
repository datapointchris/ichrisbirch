import random
from faker import Faker
from abc import ABC, abstractmethod


class FakeDataGenerator(ABC):
    """Base class for data generators"""

    def __init__(self, seed: int = None):
        self.seed = seed
        self.generated_data = None
        self.fake = Faker()

        if self.seed:
            random.seed(seed)
            Faker.seed(seed)

    @abstractmethod
    def generate(self, num_records: int) -> list[dict]:
        """Generates fake data

        This method needs to also assign the generated data to `self.generated_data`
        """

    def ids_from_generated(self, num_records: int) -> list[int]:
        if not self.generated_data:
            return AttributeError('No data has been generated')
        return random.choices(range(0, len(self.generated_data) - 1), k=num_records)

    def records_from_generated(self, num_records: int) -> list[dict]:
        if not self.generated_data:
            return AttributeError('No data has been generated')
        return random.choices(self.generated_data, k=num_records)
