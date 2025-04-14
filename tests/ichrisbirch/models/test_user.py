import pytest

from ichrisbirch import models
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


class TestDotPreferenceToNestedDict:
    def test_single_level_key(self):
        dot_key = "view_type"
        value = "grid"
        expected = {"view_type": "grid"}
        result = models.User.dot_preference_to_nested_dict(dot_key, value)
        assert result == expected

    def test_two_level_key(self):
        dot_key = "tasks.view_type"
        value = "grid"
        expected = {"tasks": {"view_type": "grid"}}
        result = models.User.dot_preference_to_nested_dict(dot_key, value)
        assert result == expected

    def test_multi_level_key(self):
        dot_key = "tasks.pages.index.view_type"
        value = "grid"
        expected = {"tasks": {"pages": {"index": {"view_type": "grid"}}}}
        result = models.User.dot_preference_to_nested_dict(dot_key, value)
        assert result == expected

    def test_empty_key(self):
        dot_key = ""
        value = "grid"
        expected = {}
        result = models.User.dot_preference_to_nested_dict(dot_key, value)
        assert result == expected

    def test_key_with_empty_parts(self):
        dot_key = "tasks..view_type"
        value = "grid"
        expected = {"tasks": {"": {"view_type": "grid"}}}
        result = models.User.dot_preference_to_nested_dict(dot_key, value)
        assert result == expected

    def test_value_is_none(self):
        dot_key = "tasks.pages.index.view_type"
        value = None
        expected = {"tasks": {"pages": {"index": {"view_type": None}}}}
        result = models.User.dot_preference_to_nested_dict(dot_key, value)
        assert result == expected

    def test_value_is_complex(self):
        dot_key = "settings.default_user_preferences"
        value = {"theme": "dark", "notifications": True}
        expected = {"settings": {"default_user_preferences": {"theme": "dark", "notifications": True}}}
        result = models.User.dot_preference_to_nested_dict(dot_key, value)
        assert result == expected
