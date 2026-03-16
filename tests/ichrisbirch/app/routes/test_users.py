import pytest
from fastapi import status

import tests.util


@pytest.mark.skip(reason='Flask route replaced by Vue; covered by frontend/e2e/profile.spec.ts')
def test_settings(test_app_logged_in):
    """Settings uses @fresh_login_required — needs fresh session."""
    response = test_app_logged_in.get('/users/settings/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
