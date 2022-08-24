from dataclasses import dataclass


@dataclass
class Config:
    SEED: int = 777
    NUM_FAKE: int = 1000
    NUM_TEST: int = 10


test_config = Config()
