import os

import pytest
from fastapi import status

from tests.helpers import show_status_and_response


@pytest.mark.skipif(
    os.environ.get('GITHUB_ACTIONS') == 'true',
    reason='AWS credentials not available on Github Actions, no plans to implement',
)
def test_get_serverstats(test_app):
    response = test_app.get('/admin/backups/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
