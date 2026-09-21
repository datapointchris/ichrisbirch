"""A timezone named the IANA way, such as `America/New_York`, never as an offset.

An offset is how far one clock stood from UTC at one moment. It cannot say what
that clock will read on a future date, or where a calendar day ends after the
next daylight-saving change. A zone name answers both, because it carries the
rules rather than one reading of them.
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
