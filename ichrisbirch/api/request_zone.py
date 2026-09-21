"""The IANA zone a request's calendar questions are answered in.

"Which day is today" and "which day does this instant fall on" have no answer
without a zone. A caller naming one in `timezone` gets it: the CLI sends the zone
of the machine it runs on. Otherwise the answer is the user's calendar zone,
which is their `timezone` preference, or UTC before the web app has set one.
"""

from typing import Annotated

from fastapi import Depends
from fastapi import Query

from ichrisbirch.api.endpoints.auth import CurrentUser
from ichrisbirch.schemas.iana_zone import IanaZone


def request_zone(
    user: CurrentUser,
    timezone: Annotated[IanaZone | None, Query(description='IANA zone for the calendar; defaults to the user preference')] = None,
) -> str:
    return timezone or user.calendar_zone


RequestZone = Annotated[str, Depends(request_zone)]
