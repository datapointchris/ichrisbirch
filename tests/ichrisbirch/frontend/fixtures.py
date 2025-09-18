from playwright.sync_api import Page

from tests.utils.database import get_test_login_users
from tests.utils.database import test_settings

FRONTEND_BASE_URL = f'{test_settings.flask.host}:{test_settings.flask.port}'


def get_test_login_user_with_password(email: str):
    for user in get_test_login_users():
        if user['email'] == email:
            return user
    raise ValueError(f'No test user found with email: {email}')


def set_defaults(page: Page):
    page.set_default_navigation_timeout(test_settings.playwright.timeout)
    page.set_default_timeout(test_settings.playwright.timeout)


def login_regular_user(page: Page):
    regular_user = get_test_login_user_with_password('testloginregular@testuser.com')
    set_defaults(page)
    page.goto(f'{FRONTEND_BASE_URL}/login/')
    page.get_by_label('Email').fill(regular_user['email'])
    page.get_by_label('Password').fill(regular_user['password'])
    page.get_by_role('button', name='Log In').click()


def login_admin_user(page: Page):
    admin_user = get_test_login_user_with_password('testloginadmin@testadmin.com')
    set_defaults(page)
    page.goto(f'{FRONTEND_BASE_URL}/login/')
    page.get_by_label('Email').fill(admin_user['email'])
    page.get_by_label('Password').fill(admin_user['password'])
    page.get_by_role('button', name='Log In').click()
