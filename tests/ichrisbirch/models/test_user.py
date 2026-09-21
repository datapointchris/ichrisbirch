import pytest

from ichrisbirch import models
from tests.test_data.users import BASE_DATA


@pytest.fixture(autouse=True)
def test_user():
    """Create a user with default preferences for testing."""
    yield BASE_DATA[0]


class TestValidatePreferences:
    def test_valid_update_shallow(self, test_user):
        update = {'theme_color': 'blue'}
        try:
            test_user.validate_preferences(key='preferences', updated_preferences=update)
        except ValueError:
            pytest.fail('validate_preference raised ValueError unexpectedly!')

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
            pytest.fail('validate_preference raised ValueError unexpectedly!')

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
            pytest.fail('validate_preference raised ValueError unexpectedly!')

    def test_mixed_valid_invalid_update(self, test_user):
        update = {
            'theme_color': 'red',
            'box_packing': {'pages': {'all': {'view_type': 'block'}}},
            'tasks': {'pages': {'index': {'view_type': 'invalid_view_type'}}},
        }
        with pytest.raises(ValueError, match="Invalid value for 'view_type'.*"):
            test_user.validate_preferences(key='preferences', updated_preferences=update)

    def test_an_iana_zone_is_a_valid_timezone(self, test_user):
        update = {'timezone': 'America/New_York'}
        assert test_user.validate_preferences(key='preferences', updated_preferences=update) == update

    def test_a_null_timezone_is_one_nobody_has_chosen(self, test_user):
        update = {'timezone': None}
        assert test_user.validate_preferences(key='preferences', updated_preferences=update) == update

    @pytest.mark.parametrize('zone', ['EST-5', 'America/New_York ', '', 'localtime', '-05:00'])
    def test_a_name_zoneinfo_cannot_load_is_refused(self, test_user, zone):
        with pytest.raises(ValueError, match='is not an IANA timezone name'):
            test_user.validate_preferences(key='preferences', updated_preferences={'timezone': zone})

    def test_a_timezone_that_is_not_a_string_is_a_value_error(self, test_user):
        """zoneinfo answers a number with a TypeError, which the endpoint would turn into a 500."""
        with pytest.raises(ValueError, match="Invalid value for 'timezone'"):
            test_user.validate_preferences(key='preferences', updated_preferences={'timezone': -5})


class TestDotPreferenceToNestedDict:
    def test_single_level_key(self):
        dot_key = 'view_type'
        value = 'grid'
        expected = {'view_type': 'grid'}
        result = models.User.dot_preference_to_nested_dict(dot_key, value)
        assert result == expected

    def test_two_level_key(self):
        dot_key = 'tasks.view_type'
        value = 'grid'
        expected = {'tasks': {'view_type': 'grid'}}
        result = models.User.dot_preference_to_nested_dict(dot_key, value)
        assert result == expected

    def test_multi_level_key(self):
        dot_key = 'tasks.pages.index.view_type'
        value = 'grid'
        expected = {'tasks': {'pages': {'index': {'view_type': 'grid'}}}}
        result = models.User.dot_preference_to_nested_dict(dot_key, value)
        assert result == expected

    def test_empty_key(self):
        dot_key = ''
        value = 'grid'
        expected = {}
        result = models.User.dot_preference_to_nested_dict(dot_key, value)
        assert result == expected

    def test_key_with_empty_parts(self):
        dot_key = 'tasks..view_type'
        value = 'grid'
        expected = {'tasks': {'': {'view_type': 'grid'}}}
        result = models.User.dot_preference_to_nested_dict(dot_key, value)
        assert result == expected

    def test_value_is_none(self):
        dot_key = 'tasks.pages.index.view_type'
        value = None
        expected = {'tasks': {'pages': {'index': {'view_type': None}}}}
        result = models.User.dot_preference_to_nested_dict(dot_key, value)
        assert result == expected

    def test_value_is_complex(self):
        dot_key = 'settings.default_user_preferences'
        value = {'theme': 'dark', 'notifications': True}
        expected = {'settings': {'default_user_preferences': {'theme': 'dark', 'notifications': True}}}
        result = models.User.dot_preference_to_nested_dict(dot_key, value)
        assert result == expected


class TestGetPreference:
    """Test get_preference() method with automatic fallback to DEFAULT_USER_PREFERENCES.

    This method should:
    1. Return user's preference if set
    2. Fall back to DEFAULT_USER_PREFERENCES if key missing from user
    3. Support dot-notation for nested keys
    4. Return None for completely unknown keys
    """

    def test_get_existing_preference(self, test_user):
        """User has the preference set - return user's value."""
        # Set a specific preference on the user
        test_user.preferences = {'theme_color': 'red', 'dark_mode': False}
        result = test_user.get_preference('theme_color')
        assert result == 'red', 'Should return user preference value'

    def test_get_missing_preference_falls_back_to_default(self, test_user):
        """User doesn't have key - fall back to DEFAULT_USER_PREFERENCES."""
        # User has empty preferences (or missing key)
        test_user.preferences = {}
        result = test_user.get_preference('dark_mode')
        # DEFAULT_USER_PREFERENCES has dark_mode: True
        assert result is True, 'Should fall back to default preference'

    def test_get_deeply_nested_preference(self, test_user):
        """Test dot-notation for nested preferences like tasks.pages.todo.view_type."""
        test_user.preferences = {}  # Empty - will fall back to defaults
        result = test_user.get_preference('tasks.pages.todo.view_type')
        # DEFAULT_USER_PREFERENCES has tasks.pages.todo.view_type: 'compact'
        assert result == 'compact', 'Should return default for nested preference'

    def test_get_nested_preference_partial_user_prefs(self, test_user):
        """User has partial nested structure - should still fall back for missing keys."""
        # User has tasks.pages.index but not tasks.pages.todo
        test_user.preferences = {'tasks': {'pages': {'index': {'view_type': 'block'}}}}
        # Asking for todo.view_type which isn't in user prefs - should fall back to default
        result = test_user.get_preference('tasks.pages.todo.view_type')
        # Should fall back to default since tasks.pages.todo doesn't exist in user prefs
        assert result == 'compact', 'Should fall back when nested path incomplete'

    def test_get_preference_with_explicit_default(self, test_user):
        """Explicit default should override DEFAULT_USER_PREFERENCES fallback."""
        test_user.preferences = {}
        result = test_user.get_preference('nonexistent.key', default='my_default')
        assert result == 'my_default', 'Explicit default should be returned'

    def test_get_completely_unknown_preference(self, test_user):
        """Key doesn't exist anywhere - return None."""
        test_user.preferences = {}
        result = test_user.get_preference('completely.unknown.key.path')
        assert result is None, 'Should return None for unknown keys'

    def test_user_preference_takes_precedence(self, test_user):
        """User's value should override default even for nested keys."""
        test_user.preferences = {
            'tasks': {
                'pages': {
                    'todo': {'view_type': 'block'}  # Override default 'compact'
                }
            }
        }
        result = test_user.get_preference('tasks.pages.todo.view_type')
        assert result == 'block', 'User preference should override default'


class TestCalendarZone:
    def test_the_preference_is_the_calendar(self, test_user):
        test_user.preferences = {'timezone': 'America/New_York'}
        assert test_user.calendar_zone == 'America/New_York'

    def test_a_user_with_no_preference_reads_days_in_utc(self, test_user):
        test_user.preferences = {'timezone': None}
        assert test_user.calendar_zone == 'UTC'

    def test_preferences_that_predate_the_key_read_days_in_utc(self, test_user):
        test_user.preferences = {'theme_color': 'blue'}
        assert test_user.calendar_zone == 'UTC'
