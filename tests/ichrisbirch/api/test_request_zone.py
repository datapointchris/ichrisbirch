"""Which zone a request's calendar is read in, without an HTTP client.

The endpoints that use it are tested through the API with the default test
user, whose preference is unset. The preference branch lives here, where a user
carrying one costs a constructor rather than a login.
"""

from ichrisbirch import models
from ichrisbirch.api.request_zone import request_zone


def user_in(zone: str | None) -> models.User:
    return models.User(name='Zone', email='zone@example.com', preferences={'timezone': zone})


def test_a_named_zone_wins_over_the_preference():
    """The CLI names the zone of the machine it runs on, and that is the calendar it prints."""
    assert request_zone(user_in('America/New_York'), timezone='Asia/Tokyo') == 'Asia/Tokyo'


def test_the_users_calendar_zone_answers_when_no_zone_is_named():
    assert request_zone(user_in('America/New_York'), timezone=None) == 'America/New_York'
    assert request_zone(user_in(None), timezone=None) == 'UTC'
