import pytest

from tests.test_data.users import BASE_DATA as test_users


@pytest.fixture(autouse=True)
def test_user():
    """Create a user with default preferences for testing."""
    yield test_users[0]


class TestValidatePreferences:

    def test_valid_update_shallow(self, test_user):
        update = {'theme_color': 'blue'}
        try:
            test_user.validate_preferences(key='preferences', updated_preferences=update)
        except ValueError:
            pytest.fail("validate_preference raised ValueError unexpectedly!")

    def test_invalid_key(self, test_user):
        update = {'non_existent_key': 'value'}
        with pytest.raises(ValueError, match="Invalid preference: 'non_existent_key'.*"):
            test_user.validate_preferences(key='preferences', updated_preferences=update)

    def test_invalid_enum_value(self, test_user):
        update = {'theme_color': 'not_a_color'}
        with pytest.raises(ValueError, match="Invalid value for 'theme_color'.*"):
            test_user.validate_preferences(key='preferences', updated_preferences=update)

    def test_valid_update_nested(self, test_user):
        update = {'box_packing': {'pages': {'all': {'view_type': 'compact'}}}}
        try:
            test_user.validate_preferences(key='preferences', updated_preferences=update)
        except ValueError:
            pytest.fail("validate_preference raised ValueError unexpectedly!")

    def test_invalid_key_in_nested_dict(self, test_user):
        update = {'box_packing': {'pages': {'all': {'non_existent_key': 'value'}}}}
        with pytest.raises(ValueError, match="Invalid preference: 'non_existent_key'.*"):
            test_user.validate_preferences(key='preferences', updated_preferences=update)

    def test_invalid_enum_value_in_nested(self, test_user):
        update = {'tasks': {'pages': {'index': {'view_type': 'invalid_view_type'}}}}
        with pytest.raises(ValueError, match="Invalid value for 'view_type'.*"):
            test_user.validate_preferences(key='preferences', updated_preferences=update)

    def test_valid_complete_update(self, test_user):
        update = {
            'theme_color': 'red',
            'box_packing': {'pages': {'all': {'view_type': 'block'}}},
            'tasks': {'pages': {'index': {'view_type': 'compact'}}},
        }
        try:
            test_user.validate_preferences(key='preferences', updated_preferences=update)
        except ValueError:
            pytest.fail("validate_preference raised ValueError unexpectedly!")

    def test_mixed_valid_invalid_update(self, test_user):
        update = {
            'theme_color': 'red',
            'box_packing': {'pages': {'all': {'view_type': 'block'}}},
            'tasks': {'pages': {'index': {'view_type': 'invalid_view_type'}}},
        }
        with pytest.raises(ValueError, match="Invalid value for 'view_type'.*"):
            test_user.validate_preferences(key='preferences', updated_preferences=update)
