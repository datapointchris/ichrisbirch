"""The IANA zone a request's calendar questions are answered in.

"Which day is today" and "which day does this instant fall on" have no answer
without a zone. A caller naming one in `timezone` gets it: the CLI sends the zone
of the machine it runs on. Otherwise the answer is the user's calendar zone,
which is their `timezone` preference, or UTC before the web app has set one. A
service has no preference, so it gets UTC unless it names a zone.
"""

from typing import Annotated

from fastapi import Depends
from fastapi import Query

from ichrisbirch import models
from ichrisbirch.api.endpoints.auth import get_current_user_or_service
from ichrisbirch.api.oidc_auth import ServicePrincipal
from ichrisbirch.models.user import CALENDAR_FALLBACK_ZONE
from ichrisbirch.schemas.iana_zone import IanaZone


def request_zone(
    caller: Annotated[models.User | ServicePrincipal, Depends(get_current_user_or_service)],
    timezone: Annotated[IanaZone | None, Query(description='IANA zone for the calendar; defaults to the user preference')] = None,
) -> str:
    if timezone:
        return timezone
    return caller.calendar_zone if isinstance(caller, models.User) else CALENDAR_FALLBACK_ZONE


RequestZone = Annotated[str, Depends(request_zone)]
