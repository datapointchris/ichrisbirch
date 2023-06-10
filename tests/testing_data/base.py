import random
from functools import cached_property
from typing import Optional, Protocol


class FakeDataGenerator(Protocol):
    """Base class for data generators

    To Implement:
        The `generate` function simply needs to return
        Set the seed to get reproducable output
    """

    total_records: int
    num_test_records: int
    seed: Optional[int]

    @cached_property
    def generated_data(self):
        """Generated fake data"""
        return self.generate()

    def generate(self) -> list[dict]:
        ...

    @property
    def random_ids(self) -> list[int]:
        """Returns a list of random record ids from generated data"""
        return random.choices(range(0, len(self.generated_data) - 1), k=self.num_test_records)

    @property
    def random_records(self) -> list[dict]:
        """Returns a list of random records from generated data"""
        return random.choices(self.generated_data, k=self.num_test_records)
