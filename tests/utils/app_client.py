# import logging

# import pytest
# from flask_login import FlaskLoginClient
# from flask_login import login_user

# from ichrisbirch.app.main import create_app
# from tests.environment import get_test_runner_settings
# from tests.utils.database import get_test_login_admin_user
# from tests.utils.database import get_test_login_regular_user

# logger = logging.getLogger(__name__)
# test_settings = get_test_runner_settings()


# class FlaskClientAPIHeaders(FlaskLoginClient):
#     """A Flask test client that allows for setting API headers."""

#     def __init__(self, *args, **kwargs):
#         self.api_headers = kwargs.pop('api_headers', {})
#         super().__init__(*args, **kwargs)

#     def open(self, *args, **kwargs):
#         headers = kwargs.pop('headers', {})
#         headers.update(self.api_headers)
#         kwargs['headers'] = headers
#         return super().open(*args, **kwargs)


# def create_test_app_base():
#     """This is used for the test client and also for tests/wsgi_app.py for Gunicorn."""
#     app = create_app(settings=test_settings)
#     app.config.update({'TESTING': True, 'WTF_CSRF_ENABLED': False})
#     return app


# def create_test_app_client(login=False, admin=False):
#     """Create a Flask test client with optional user login."""
#     app = create_test_app_base()
#     if login:
#         app.test_client_class = FlaskClientAPIHeaders
#         user = get_test_login_admin_user() if admin else get_test_login_regular_user()
#         api_headers = {'X-Application-ID': test_settings.flask.app_id, 'X-User-ID': user.get_id()}
#         with app.test_request_context():
#             login_user(user)
#             client = app.test_client(user=user, api_headers=api_headers)
#             logger.info(f'Logged in {"admin" if admin else "user"} to test app: {user.email}: {user.get_id()}')
#             return client
#     return app.test_client()
