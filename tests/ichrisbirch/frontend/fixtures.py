from playwright.sync_api import Page

from ichrisbirch.config import get_settings
from tests.util import TEST_LOGIN_ADMIN_USER
from tests.util import TEST_LOGIN_REGULAR_USER

settings = get_settings()

FRONTEND_BASE_URL = f'{settings.flask.host}:{settings.flask.port}'


def set_defaults(page: Page):
    page.set_default_navigation_timeout(settings.playwright.timeout)
    page.set_default_timeout(settings.playwright.timeout)


def login(page: Page):
    set_defaults(page)
    page.goto(f'{FRONTEND_BASE_URL}/login/')
    page.get_by_label('Email').fill(TEST_LOGIN_REGULAR_USER['email'])
    page.get_by_label('Password').fill(TEST_LOGIN_REGULAR_USER['password'])
    page.get_by_role('button', name='Log In').click()


def login_admin(page: Page):
    set_defaults(page)
    page.goto(f'{FRONTEND_BASE_URL}/login/')
    page.get_by_label('Email').fill(str(TEST_LOGIN_ADMIN_USER['email']))
    page.get_by_label('Password').fill(str(TEST_LOGIN_ADMIN_USER['password']))
    page.get_by_role('button', name='Log In').click()
