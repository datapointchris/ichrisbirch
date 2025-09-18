import re

from playwright.sync_api import Page
from playwright.sync_api import expect

from tests.ichrisbirch.frontend.fixtures import login_admin_user
from tests.ichrisbirch.frontend.fixtures import login_regular_user

welcome = re.compile(r'Welcome, *')


def test_login_regular_user(page: Page):
    login_regular_user(page)
    expect(page).to_have_title(welcome)


def test_login_admin_user(page: Page):
    login_admin_user(page)
    expect(page).to_have_title(welcome)
