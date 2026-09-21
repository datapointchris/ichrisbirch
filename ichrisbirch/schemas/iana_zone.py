"""A timezone named the IANA way, such as `America/New_York`, never as an offset.

An event's zone has to say what its venue's clock reads next March, and a
request's zone has to say where a day ends after the next daylight-saving
change. An offset records one moment's distance from UTC and answers neither.
"""

from typing import Annotated
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError

from pydantic import AfterValidator


def refuse_unknown_zone(name: str) -> str:
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as e:
        raise ValueError(f'{name!r} is not an IANA timezone name, e.g. America/New_York') from e
    return name


IanaZone = Annotated[str, AfterValidator(refuse_unknown_zone)]
