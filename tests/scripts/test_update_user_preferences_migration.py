import pytest

from scripts.update_user_preferences_migration import fill_missing_default_preferences
from scripts.update_user_preferences_migration import prune_unused_preferences
from scripts.update_user_preferences_migration import update_preference_keys
from scripts.update_user_preferences_migration import update_preferences
from tests.test_data.users import BASE_DATA as test_users


@pytest.fixture(autouse=True)
def test_user():
    """Create a user with default preferences for testing."""
    yield test_users[0]


class TestFillMissingDefaultPreferences:
    def test_fill_missing_keys(self):
        user_prefs = {'a': 1, 'b': {'ba': 21}}
        default_prefs = {'a': 0, 'b': {'ba': 20, 'bb': 22}, 'c': 3}
        expected = {'a': 1, 'b': {'ba': 21, 'bb': 22}, 'c': 3}
        result = fill_missing_default_preferences(user_prefs, default_prefs)
        assert result == expected

    def test_no_missing_keys(self):
        user_prefs = {'a': 1, 'b': {'ba': 21, 'bb': 22}, 'c': 3}
        default_prefs = {'a': 0, 'b': {'ba': 20, 'bb': 22}, 'c': 3}
        result = fill_missing_default_preferences(user_prefs, default_prefs)
        assert result == user_prefs  # No changes if no missing keys

    def test_empty_user_prefs(self):
        user_prefs = {}
        default_prefs = {'a': 0, 'b': {'ba': 20, 'bb': 22}, 'c': 3}
        result = fill_missing_default_preferences(user_prefs, default_prefs)
        assert result == default_prefs


class TestUpdatePreferenceKeys:
    def test_update_keys(self):
        user_prefs = {'old_key1': 1, 'nested': {'old_key2': 2}}
        default_prefs = {'new_key1': 0, 'nested': {'new_key2': 0}}
        transfer_map = {'old_key1': 'new_key1', 'nested.old_key2': 'nested.new_key2'}
        expected = {'new_key1': 1, 'nested': {'new_key2': 2}}
        result = update_preference_keys(user_prefs, default_prefs, transfer_map)
        assert result == expected

    def test_update_keys_no_nested_default(self):
        user_prefs = {'old_key1': 1, 'nested': {'old_key2': 2}}
        default_prefs = {'new_key1': 0, 'nested': {'old_key2': 0}}
        transfer_map = {'old_key1': 'new_key1', 'nested.old_key2': 'nested.new_key2'}
        with pytest.raises(KeyError):
            update_preference_keys(user_prefs, default_prefs, transfer_map)
            # Expecting KeyError because nested.new_key2 is not in default_prefs

    def test_no_applicable_transfer(self):
        user_prefs = {'static_key': 1}
        default_prefs = {'static_key': 0}
        transfer_map = {'unused_key': 'transferred_key'}
        result = update_preference_keys(user_prefs, default_prefs, transfer_map)
        assert result == user_prefs  # No changes if transfer keys not present

    def test_partial_transfer(self):
        user_prefs = {'old_key1': 1, 'nested': {'preserve_key': 3}}
        default_prefs = {'new_key1': 0, 'nested': {'preserve_key': 0}}
        transfer_map = {'old_key1': 'new_key1', 'nested.old_key2': 'new_key2'}
        expected = {'new_key1': 1, 'nested': {'preserve_key': 3}}
        result = update_preference_keys(user_prefs, default_prefs, transfer_map)
        assert result == expected

    def test_transfer_overlapping_key(self):
        user_prefs = {'old_key1': 1, 'old_key2': 2}
        default_prefs = {'new_key': 0, 'old_key2': 0}
        transfer_map = {'old_key1': 'new_key', 'old_key2': 'new_key'}
        expected = {'new_key': 2}  # Last transferred key should overwrite
        result = update_preference_keys(user_prefs, default_prefs, transfer_map)
        assert result == expected

    def test_transfer_overlapping_key_no_default(self):
        user_prefs = {'old_key1': 1, 'old_key2': 2}
        default_prefs = {'old_key1': 0, 'old_key2': 0}
        transfer_map = {'old_key1': 'new_key', 'old_key2': 'new_key'}
        with pytest.raises(KeyError):
            update_preference_keys(user_prefs, default_prefs, transfer_map)
            # Expecting KeyError because new_key is not in default_prefs

    def test_nested_conflict_transfer(self):
        user_prefs = {'nested': {'old_key': {'deep_key1': 'value1'}}}
        default_prefs = {'nested': {'new_key': {'deep_key2': 'default_value'}}}
        transfer_map = {'nested.old_key.deep_key1': 'nested.new_key.deep_key2'}
        expected = {'nested': {'new_key': {'deep_key2': 'value1'}, 'old_key': {}}}
        result = update_preference_keys(user_prefs, default_prefs, transfer_map)
        assert result == expected

    def test_nested_conflict_transfe_no_default(self):
        user_prefs = {'nested': {'old_key': {'deep_key1': 'value1'}}}
        default_prefs = {'nested': {'new_key': {}}}
        transfer_map = {'nested.old_key.deep_key1': 'nested.new_key.deep_key2'}
        with pytest.raises(KeyError):
            update_preference_keys(user_prefs, default_prefs, transfer_map)
            # Expecting KeyError because deep_key2 is not in default_prefs

    def test_nested_conflict_not_empty_old_key_transfer(self):
        user_prefs = {'nested': {'old_key': {'deep_key1': 'value1', 'key_that_stays': 'value2'}}}
        default_prefs = {'nested': {'old_key': {'key_that_stays': 'value2'}, 'new_key': {'deep_key2': 'default_value'}}}
        transfer_map = {'nested.old_key.deep_key1': 'nested.new_key.deep_key2'}
        expected = {'nested': {'old_key': {'key_that_stays': 'value2'}, 'new_key': {'deep_key2': 'value1'}}}
        result = update_preference_keys(user_prefs, default_prefs, transfer_map)
        assert result == expected

    def test_deep_nested_transfer(self):
        user_prefs = {'a': {'b': {'old_key': 'value'}}}
        default_prefs = {'c': {'d': {'new_key': 'default_value'}}}
        transfer_map = {'a.b.old_key': 'c.d.new_key'}
        expected = {'a': {'b': {}}, 'c': {'d': {'new_key': 'value'}}}
        result = update_preference_keys(user_prefs, default_prefs, transfer_map)
        assert result == expected

    def test_deep_nested_not_empty_transfer(self):
        user_prefs = {'a': {'b': {'old_key': 'old_value', 'key_that_stays': 'value2'}}}
        default_prefs = {
            'a': {'b': {}, 'c': {'d': {'new_key': 'default_value'}}},
            'c': {'d': {'new_key': 'default_value'}},
        }
        transfer_map = {'a.b.old_key': 'c.d.new_key'}
        expected = {
            'a': {'b': {'key_that_stays': 'value2'}},
            'c': {'d': {'new_key': 'old_value'}},
        }
        result = update_preference_keys(user_prefs, default_prefs, transfer_map)
        assert result == expected

    def test_deep_nested_ancestor_not_empty_transfer(self):
        user_prefs = {'a': {'b': {'old_key': 'value'}, 'c': 'keep_me'}}
        default_prefs = {'a': {'c': 'default_keep_me'}, 'c': {'d': {'new_key': 'default_value'}}}
        transfer_map = {'a.b.old_key': 'c.d.new_key'}
        expected = {'a': {'b': {}, 'c': 'keep_me'}, 'c': {'d': {'new_key': 'value'}}}
        result = update_preference_keys(user_prefs, default_prefs, transfer_map)
        assert result == expected

    def test_deep_nested_remove_one_key_keep_other_transfer(self):
        user_prefs = {'a': {'b': {'old_key': 'value', 'no_delete_key': 'keep_in_old'}, 'c': 'keep_me'}}
        default_prefs = {
            'a': {'b': {'no_delete_key': 'keep_in_old'}, 'c': 'default_keep_me'},
            'c': {'d': {'new_key': 'default_value'}},
        }
        transfer_map = {'a.b.old_key': 'c.d.new_key'}
        expected = {'a': {'b': {'no_delete_key': 'keep_in_old'}, 'c': 'keep_me'}, 'c': {'d': {'new_key': 'value'}}}
        result = update_preference_keys(user_prefs, default_prefs, transfer_map)
        assert result == expected

    def test_empty_transfer_map(self):
        user_prefs = {'static_key': 1}
        default_prefs = {'static_key': 0}
        transfer_map = {}
        result = update_preference_keys(user_prefs, default_prefs, transfer_map)
        assert result == user_prefs  # No transfer if map is empty


class TestPruneUnusedPreferences:
    def test_prune_unused_keys(self):
        user_prefs = {'a': 1, 'b': 2, 'c': 3}
        default_prefs = {'a': 0, 'c': 3}
        expected = {'a': 1, 'c': 3}
        result = prune_unused_preferences(user_prefs, default_prefs)
        assert result == expected

    def test_no_prune_when_all_keys_used(self):
        user_prefs = {'a': 1, 'b': 2}
        default_prefs = {'a': 0, 'b': 2, 'c': 3}
        result = prune_unused_preferences(user_prefs, default_prefs)
        assert result == user_prefs  # No changes if all keys required

    def test_empty_user_prefs(self):
        user_prefs = {}
        default_prefs = {'a': 0}
        result = prune_unused_preferences(user_prefs, default_prefs)
        assert result == {}  # No changes if user_prefs is empty


class TestUpdatePreferences:
    def test_update_preferences(self):
        user_prefs = {'a': 1, 'b': 2}
        default_prefs = {'a': 0, 'b': 2, 'c': 3}
        updated_prefs = update_preferences(user_prefs, default_prefs)
        assert updated_prefs == {'a': 1, 'b': 2, 'c': 3}

    def test_update_preferences_with_empty_user_prefs(self):
        user_prefs = {}
        default_prefs = {'a': 0, 'b': 2, 'c': 3}
        updated_prefs = update_preferences(user_prefs, default_prefs)
        assert updated_prefs == {'a': 0, 'b': 2, 'c': 3}

    def test_update_preferences_with_deep_nested_default_prefs(self):
        user_prefs = {'a': 1}
        default_prefs = {'a': 0, 'b': {'c': 2}}
        updated_prefs = update_preferences(user_prefs, default_prefs)
        assert updated_prefs == {'a': 1, 'b': {'c': 2}}

    def test_update_preferences_with_transfer_map(self):
        user_prefs = {'old_key': 1}
        default_prefs = {'new_key': 2}
        transfer_map = {'old_key': 'new_key'}
        updated_prefs = update_preferences(user_prefs, default_prefs, transfer_map)
        assert updated_prefs == {'new_key': 1}

    def test_update_preferences_with_deep_nested_and_transfer_map(self):
        user_prefs = {'a': {'old_key': 1}}
        default_prefs = {'a': {'new_key': 2}}
        transfer_map = {'a.old_key': 'a.new_key'}
        updated_prefs = update_preferences(user_prefs, default_prefs, transfer_map)
        assert updated_prefs == {'a': {'new_key': 1}}

    def test_update_preferences_key_error_if_default_is_empty(self):
        # d key is empty in defaults, erase the transfer key
        # a.g should also be erased since it is not in the default
        user_prefs = {'a': {'b': {'old_key': 'value'}, 'c': 'keep_me'}, 'f': {'nested': 'value'}}
        default_prefs = {'a': {'b': {'default_key': 'was_missing'}, 'c': 'keep_me', 'd': {}, 'e': 'value'}}
        transfer_map = {'a.b.old_key': 'c.d.new_key', 'a.f.nested': 'a.g.new_nested'}
        with pytest.raises(KeyError):
            update_preferences(user_prefs, default_prefs, transfer_map)
            # Expecting KeyError because c.d does not have new_key value in default_prefs

    def test_update_preferences_complex_with_transfer_map(self):
        # d key has new transfer key, should transfer the value
        # a.g also has default value, should transfer the value
        user_prefs = {'a': {'b': {'old_key': 'value'}, 'c': 'keep_me'}, 'f': {'nested': 'value'}}
        default_prefs = {
            'a': {
                'b': {'default_key': 'was_missing'},
                'c': 'keep_me',
                'd': {'new_key': 'default_value'},
                'e': 'value',
                'f': {'nested': 'value'},
                'g': {'new_nested': ''},
            },
            'c': {'d': {'new_key': 'default'}},
        }
        transfer_map = {'a.b.old_key': 'c.d.new_key', 'a.f.nested': 'a.g.new_nested'}
        expected = {
            'a': {
                'b': {'default_key': 'was_missing'},
                'c': 'keep_me',
                'd': {'new_key': 'default_value'},
                'e': 'value',
                'f': {},
                'g': {'new_nested': 'value'},
            },
            'c': {'d': {'new_key': 'value'}},
        }
        updated_prefs = update_preferences(user_prefs, default_prefs, transfer_map)
        assert updated_prefs == expected

    def test_update_preferences_complex_transfer_key_missing_from_defaults(self):
        # d key is missing from defaults, should delete even after assigning from transfer
        user_prefs = {'a': {'b': {'old_key': 'value'}, 'c': 'keep_me'}}
        default_prefs = {'a': {'b': {'default_key': 'was_missing'}, 'c': 'default', 'e': 'value', 'f': {'nested': 'value'}}}
        transfer_map = {'a.b.old_key': 'c.d.new_key', 'a.f.nested': 'a.g.new_nested'}
        with pytest.raises(KeyError):
            update_preferences(user_prefs, default_prefs, transfer_map)
            # Expecting KeyError because c.d does not have new_key value in default_prefs
