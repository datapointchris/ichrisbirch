# import logging
# from contextlib import contextmanager

# from fastapi.testclient import TestClient

# from ichrisbirch.api.endpoints import auth
# from ichrisbirch.api.main import create_api
# from ichrisbirch.database.sqlalchemy.session import get_sqlalchemy_session
# from tests.conftest import test_settings
# from tests.conftest import get_test_session
# from tests.utils.database import get_test_login_admin_user
# from tests.utils.database import get_test_login_regular_user

# logger = logging.getLogger(__name__)
# test_settings = get_test_runner_settings()


# @contextmanager
# def create_test_api_client(login=False, admin=False):
#     api = create_api(settings=test_settings)
#     client = TestClient(api)

#     if login:
#         user = get_test_login_admin_user() if admin else get_test_login_regular_user()
#         api.dependency_overrides[auth.get_current_user] = lambda: user
#         api.dependency_overrides[auth.get_admin_user] = lambda: user
#         api.dependency_overrides[get_sqlalchemy_session] = get_test_session
#         logger.info(f'Logged in {"admin" if admin else "regular"} user to test api: {user.email}')
#     yield client
