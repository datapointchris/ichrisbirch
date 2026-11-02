"""The test suite. Importing it configures the run from the committed `testing.env` beside it."""

from pathlib import Path

import dotenv

TESTING_CONFIG = Path(__file__).with_name('testing.env')

# Every value already in the process environment wins over the file.
if not dotenv.load_dotenv(TESTING_CONFIG):
    raise FileNotFoundError(f'{TESTING_CONFIG} is missing or empty, and every test run is configured from it.')
