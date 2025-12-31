import pytest
from fastapi import status
from sqlalchemy import delete

from ichrisbirch import models
from tests.factories import UserFactory
from tests.factories import clear_factory_session
from tests.factories import set_factory_session
from tests.util import show_status_and_response
from tests.utils.database import create_session
from tests.utils.database import get_test_login_users
from tests.utils.database import test_settings

# Known test user credentials for login testing
TEST_USER_EMAIL = 'test_login_user@test.com'
TEST_USER_PASSWORD = 'test_login_password'
TEST_USER_NAME = 'Test Login User'

SIGNUP_USER = {
    'name': 'Signup User',
    'email': 'signup.user@gmail.com',
    'password': 'easypa_$ssword',
    'confirm_password': 'easypa_$ssword',
}


@pytest.fixture(autouse=True)
def setup_test_users(insert_users_for_login):
    """Create test users using factories for this test module.

    Uses factory-boy to create users with known credentials.
    Cleanup deletes all users except the login users (used by Flask test client).
    """
    with create_session(test_settings) as session:
        set_factory_session(session)
        UserFactory(name=TEST_USER_NAME, email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
        session.commit()
        clear_factory_session()

    yield

    # Cleanup: delete all test users except login users
    with create_session(test_settings) as session:
        login_emails = [user['email'] for user in get_test_login_users()]
        session.execute(delete(models.User).where(models.User.email.notin_(login_emails)))
        session.commit()


@pytest.fixture()
def test_app_with_logout_function(test_app_function):
    yield test_app_function
    test_app_function.get('/logout/')


class TestLogin:
    def test_login_page(self, test_app_function):
        response = test_app_function.get('/login/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert b'<title>Login for iChrisBirch</title>' in response.data

    def test_login_page_redirects_for_logged_in_user(self, test_app_logged_in_function):
        response = test_app_logged_in_function.get('/login/')
        assert response.status_code == status.HTTP_302_FOUND, show_status_and_response(response)
        assert '/users/profile/' in response.headers['Location']

    def test_do_login(self, test_app_function):
        login_data = {'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        response = test_app_function.post('/login/', follow_redirects=True, data=login_data)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert f'<title>Welcome, {TEST_USER_NAME}</title>' in response.text

    def test_login_wrong_password(self, test_app_function, caplog):
        login_data = {'email': TEST_USER_EMAIL, 'password': 'wrong_password'}
        response = test_app_function.post('/login/', follow_redirects=False, data=login_data)
        assert 'invalid password' in caplog.text, 'No error log produced'
        assert response.status_code == status.HTTP_302_FOUND, show_status_and_response(response)
        assert 'login' in response.headers['Location']


class TestSignup:
    def test_signup_page(self, test_app_function):
        response = test_app_function.get('/signup/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert b'<title>Signup for iChrisBirch</title>' in response.data

    def test_do_signup(self, test_app_function):
        response = test_app_function.post('/signup/', follow_redirects=True, data=SIGNUP_USER)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert f'<title>Welcome, {SIGNUP_USER["name"]}</title>' in response.text

    def test_duplicate_signup_error(self, test_app_function, caplog):
        test_app_function.post(
            '/signup/',
            follow_redirects=True,
            data={
                'name': TEST_USER_NAME,
                'email': TEST_USER_EMAIL,
                'password': TEST_USER_PASSWORD,
                'confirm_password': TEST_USER_PASSWORD,
            },
        )
        assert 'duplicate email registration attempt' in caplog.text
