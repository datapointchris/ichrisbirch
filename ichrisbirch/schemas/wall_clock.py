"""A reading on a clock at a place, kept as read and never converted.

19:00 at a venue is 19:00 for everyone reading about it, so the reading is
stored naive and an `IanaZone` beside it names the clock. A caller that sends an
offset anyway is describing the same reading, so the offset is dropped.
Converting it instead would move 19:00 to whatever that instant reads in another
zone.
"""

import datetime as dt
from typing import Annotated

from pydantic import AfterValidator


def drop_offset(reading: dt.datetime) -> dt.datetime:
    return reading.replace(tzinfo=None)


WallClock = Annotated[dt.datetime, AfterValidator(drop_offset)]
