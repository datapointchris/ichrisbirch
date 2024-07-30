ALL_ACCESS = '/'
USER_ACCESS = '/users/profile/'
ADMIN_ACCESS = '/admin/'


class TestHomeAccess:
    def test_anonymous_access_home(self, test_app_function):
        response = test_app_function.get(ALL_ACCESS)
        assert response.status_code == 200

    def test_login_access_home(self, test_app_logged_in_function):
        response = test_app_logged_in_function.get(ALL_ACCESS)
        assert response.status_code == 200

    def test_admin_access_home(self, test_app_logged_in_admin_function):
        response = test_app_logged_in_admin_function.get(ALL_ACCESS)
        assert response.status_code == 200


class TestProfileAccess:
    def test_anonymous_no_access_profile(self, test_app_function):
        response = test_app_function.get(USER_ACCESS)
        assert response.status_code != 200

    def test_login_access_profile(self, test_app_logged_in_function):
        response = test_app_logged_in_function.get(USER_ACCESS)
        assert response.status_code == 200

    def test_admin_access_profile(self, test_app_logged_in_admin_function):
        response = test_app_logged_in_admin_function.get(USER_ACCESS)
        assert response.status_code == 200


class TestAdminAccess:
    def test_anonymous_no_access_admin(self, test_app_function):
        response = test_app_function.get(ADMIN_ACCESS)
        assert response.status_code != 200

    def test_no_admin_no_access_admin(self, test_app_logged_in_function):
        response = test_app_logged_in_function.get(ADMIN_ACCESS)
        assert response.status_code != 200

    def test_admin_access_admin(self, test_app_logged_in_admin_function):
        response = test_app_logged_in_admin_function.get(ADMIN_ACCESS)
        assert response.status_code == 200
