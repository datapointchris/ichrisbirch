import logging

import httpx
import pendulum
import streamlit as st

from ichrisbirch import models
from ichrisbirch.app.utils import url_builder
from ichrisbirch.config import get_settings

settings = get_settings('development')
logger = logging.getLogger('chat.login')
http_client = httpx.Client()

TOKEN_URL = f'{settings.api_url}/auth/token/'
USERS_URL = f'{settings.api_url}/users/'


def initialize_session():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "refresh_token" not in st.session_state:
        st.session_state.refresh_token = None


def require_user_logged_in():
    logger.info('initializing session')
    initialize_session()
    if not st.session_state.access_token or not validate_jwt_token(st.session_state.access_token):
        logger.info('no access token found, or token is invalid, trying to refresh')
        if not refresh_access_token():
            logger.info('failed to refresh access token, displaying login form')
            display_login_form()
            if not st.session_state.logged_in:
                return False
    return True


def validate_jwt_token(token: str):
    logger.info(f'validating access token: {token}')
    response = http_client.get(url_builder(TOKEN_URL, 'validate'), headers={'Authorization': f'Bearer {token}'})
    return response.status_code == httpx.codes.OK


def refresh_access_token():
    if not st.session_state.refresh_token:
        st.session_state.logged_in = False
        return False
    headers = {'Authorization': f'Bearer {st.session_state.refresh_token}'}
    logger.info(f'refreshing access token with refresh token: {st.session_state.refresh_token}')
    response = http_client.post(url_builder(TOKEN_URL, 'refresh'), headers=headers)
    if response.status_code == httpx.codes.OK:
        st.session_state.access_token = response.json().get("access_token")
        return True
    else:
        st.error('Failed to refresh access token')
        logger.error('Failed to refresh access token')
        st.session_state.logged_in = False
        return False


def display_login_form():
    with st.form("LoginForm"):
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.form_submit_button("Log in", on_click=login_flow)


def login_flow():
    user = login_user()
    if user and request_jwt_tokens(user):
        st.session_state.logged_in = True
        logger.info(f'user logged in: {user.name}')
    else:
        st.error('Invalid username or password')
        logger.warning(f'Invalid login attempt for: {st.session_state["username"]}')
    st.session_state.pop("username", None)
    st.session_state.pop("password", None)


def login_user():
    response = http_client.get(url_builder(USERS_URL, 'email', st.session_state['username']))
    if user_data := response.raise_for_status().json():
        user = models.User(**user_data)
    if user and user.check_password(password=st.session_state['password']):
        logger.debug(f'logged in user: {user.name} - last previous login: {user.last_login}')
        http_client.patch(url_builder(USERS_URL, user.id), json={'last_login': pendulum.now().for_json()})
        return user
    return None


def logout_user():
    headers = {'Authorization': f'Bearer {st.session_state.get('access_token')}'}
    http_client.get(url_builder(settings.api_url, 'auth', 'logout'), headers=headers)
    st.session_state.logged_in = False
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    logger.info('user logged out')


def request_jwt_tokens(user: models.User):
    request_data = {'username': user.email, 'password': st.session_state['password']}
    response = http_client.post(TOKEN_URL, data=request_data)
    if response.status_code == httpx.codes.CREATED:
        tokens = response.json()
        st.session_state.access_token = tokens.get("access_token")
        st.session_state.refresh_token = tokens.get("refresh_token")
        logger.info(f'JWT tokens received for user: {user.name}')
        return True
    else:
        response_detail = response.json().get('detail')
        logger.error(f'Failed to obtain JWT tokens: {response_detail}')
        st.error('Failed to obtain JWT tokens')
        return False
