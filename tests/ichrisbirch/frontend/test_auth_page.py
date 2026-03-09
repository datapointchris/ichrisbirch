import re

import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect
from sqlalchemy import delete
from sqlalchemy import select

from ichrisbirch import models
from tests.ichrisbirch.frontend.fixtures import FRONTEND_BASE_URL
from tests.ichrisbirch.frontend.fixtures import login_regular_user
from tests.ichrisbirch.frontend.fixtures import set_defaults
from tests.utils.database import create_session
from tests.utils.database import get_test_login_users
from tests.utils.database import test_settings

SIGNUP_USER = {
    'name': 'Playwright Signup User',
    'email': 'playwright.signup@test.com',
    'password': 'playwright_test_pass',
}


@pytest.fixture(autouse=True)
def setup_auth_tests(insert_users_for_login):
    """Ensure login users exist. Cleanup any users created during tests."""
    yield

    with create_session(test_settings) as session:
        login_emails = [user['email'] for user in get_test_login_users()]
        session.execute(delete(models.User).where(models.User.email.notin_(login_emails)))
        session.commit()


@pytest.fixture(autouse=True)
def setup_page(setup_auth_tests, page: Page):
    set_defaults(page)


def test_login_page_loads(page: Page):
    page.goto(f'{FRONTEND_BASE_URL}/login/')
    expect(page).to_have_title('Login for iChrisBirch')


def test_login_success(page: Page):
    """Login with valid credentials, verify redirect to profile."""
    login_regular_user(page)
    expect(page).to_have_title(re.compile(r'Welcome,'))


def test_login_wrong_password(page: Page):
    """Login with wrong password, verify error message appears."""
    page.goto(f'{FRONTEND_BASE_URL}/login/')
    page.get_by_label('Email').fill('testloginregular@testuser.com')
    page.get_by_label('Password').fill('wrong_password')
    page.get_by_role('button', name='Log In').click()

    # Should stay on login page with error
    expect(page).to_have_title('Login for iChrisBirch')
    expect(page.locator('body')).to_contain_text('Invalid credentials')


def test_login_nonexistent_user(page: Page):
    """Login with a nonexistent email, verify error message."""
    page.goto(f'{FRONTEND_BASE_URL}/login/')
    page.get_by_label('Email').fill('nobody@nowhere.com')
    page.get_by_label('Password').fill('doesntmatter')
    page.get_by_role('button', name='Log In').click()

    expect(page).to_have_title('Login for iChrisBirch')
    expect(page.locator('body')).to_contain_text('Invalid credentials')


def test_protected_page_redirects_to_login(page: Page):
    """Accessing a protected page while logged out should redirect to login."""
    page.goto(f'{FRONTEND_BASE_URL}/tasks/')
    # Should end up on the login page
    expect(page).to_have_title('Login for iChrisBirch')


def test_logout(page: Page):
    """Login, then logout, verify we can no longer access protected pages."""
    login_regular_user(page)
    expect(page).to_have_title(re.compile(r'Welcome,'))

    page.goto(f'{FRONTEND_BASE_URL}/logout/')
    # After logout, trying to access a protected page should redirect to login
    page.goto(f'{FRONTEND_BASE_URL}/tasks/')
    expect(page).to_have_title('Login for iChrisBirch')


def test_signup_page_loads(page: Page):
    page.goto(f'{FRONTEND_BASE_URL}/signup/')
    expect(page).to_have_title('Signup for iChrisBirch')


def test_signup_success(page: Page):
    """Sign up a new user, verify redirect to profile and user in DB."""
    page.goto(f'{FRONTEND_BASE_URL}/signup/')

    page.get_by_label('Name').fill(SIGNUP_USER['name'])
    page.get_by_label('Email').fill(SIGNUP_USER['email'])
    page.locator('#password').fill(SIGNUP_USER['password'])
    page.locator('#confirm_password').fill(SIGNUP_USER['password'])
    page.get_by_role('button', name='Sign Up').click()

    # Should be logged in and on profile page
    expect(page).to_have_title(f'Welcome, {SIGNUP_USER["name"]}')

    # Verify user exists in DB
    with create_session(test_settings) as session:
        user = session.execute(select(models.User).where(models.User.email == SIGNUP_USER['email'])).scalar_one()
        assert user.name == SIGNUP_USER['name']


def test_signup_duplicate_email(page: Page):
    """Sign up with an existing email, verify error message."""
    page.goto(f'{FRONTEND_BASE_URL}/signup/')

    page.get_by_label('Name').fill('Duplicate User')
    page.get_by_label('Email').fill('testloginregular@testuser.com')
    page.locator('#password').fill('somepassword')
    page.locator('#confirm_password').fill('somepassword')
    page.get_by_role('button', name='Sign Up').click()

    # Should stay on signup page with error
    expect(page).to_have_title('Signup for iChrisBirch')
    expect(page.locator('body')).to_contain_text('email address already registered')


def test_login_signup_login_lifecycle(page: Page):
    """Sign up a new user, logout, then login with those credentials."""
    # Sign up
    page.goto(f'{FRONTEND_BASE_URL}/signup/')
    page.get_by_label('Name').fill('Lifecycle User')
    page.get_by_label('Email').fill('lifecycle@test.com')
    page.locator('#password').fill('lifecycle_pass')
    page.locator('#confirm_password').fill('lifecycle_pass')
    page.get_by_role('button', name='Sign Up').click()

    expect(page).to_have_title('Welcome, Lifecycle User')

    # Logout
    page.goto(f'{FRONTEND_BASE_URL}/logout/')

    # Login with the new credentials
    page.goto(f'{FRONTEND_BASE_URL}/login/')
    page.get_by_label('Email').fill('lifecycle@test.com')
    page.get_by_label('Password').fill('lifecycle_pass')
    page.get_by_role('button', name='Log In').click()

    expect(page).to_have_title('Welcome, Lifecycle User')
