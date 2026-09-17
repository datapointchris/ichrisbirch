"""The assertion-message helper has to survive the responses it is called to describe.

It runs inside failing assertions, so a body it cannot parse must come back as a
placeholder rather than raise over the failure it was printing.
"""

import httpx2

from tests.util import show_status_and_response

REQUEST = httpx2.Request('GET', 'http://test/')


def test_an_empty_body_reports_the_status_with_a_placeholder():
    response = httpx2.Response(204, request=REQUEST)

    assert show_status_and_response(response) == {'HTTP_204_NO_CONTENT': '<no response content>'}


def test_a_non_json_body_reports_the_status_with_a_placeholder():
    response = httpx2.Response(500, request=REQUEST, html='<html>boom</html>')

    assert show_status_and_response(response) == {'HTTP_500_INTERNAL_SERVER_ERROR': '<no response content>'}


def test_a_json_body_is_returned_under_its_status():
    response = httpx2.Response(400, request=REQUEST, json={'detail': 'bad'})

    assert show_status_and_response(response) == {'HTTP_400_BAD_REQUEST': {'detail': 'bad'}}
