from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch.database.sqlalchemy.session import SessionLocal
from ichrisbirch.models.user import DEFAULT_USER_PREFERENCES


def fill_missing_default_preferences(user_prefs: dict, default_prefs: dict) -> dict:
    """Recursively add missing preferences from DEFAULT_USER_PREFERENCES to user preferences.

    Args:
        user_prefs (dict): The user's current preferences.
        default_prefs (dict): The default preferences.

    Returns:
        dict: Updated preferences with missing defaults added.
    """
    updated_prefs = user_prefs.copy()
    for key, default_value in default_prefs.items():
        if key not in updated_prefs:
            updated_prefs[key] = default_value
        elif isinstance(default_value, dict) and isinstance(updated_prefs.get(key), dict):
            # Recurse into nested dictionaries
            updated_prefs[key] = fill_missing_default_preferences(updated_prefs[key], default_value)
    return updated_prefs


def update_preference_keys(user_prefs: dict, default_prefs: dict, transfer_map: dict) -> dict:
    """Rename keys in user preferences based on the transfer map, leaving old keys empty.

    Args:
        user_prefs (dict): The user's current preferences.
        transfer_map (dict): A mapping of old preference keys to new preference keys.
            In the form of `{'old.nest.key': 'old.nest.new_key'}`
        default_prefs (dict): The default preferences.

    Returns:
        dict: Updated preferences with keys renamed, leaving old keys empty.

    Raises:
        KeyError: If a key in the transfer map does not exist in default preferences.
    """
    updated_prefs = user_prefs.copy()

    for old_key, new_key in transfer_map.items():
        # Traverse the old key path
        keys = old_key.split('.')
        current = updated_prefs
        for key in keys[:-1]:
            current = current.setdefault(key, {})

        # Get the value and set the new key path
        value = current.pop(keys[-1], None)
        if value is not None:
            # Check if the new key exists in default_prefs
            new_keys = new_key.split('.')
            new_current = default_prefs
            for new_key_part in new_keys:
                if new_key_part not in new_current:
                    raise KeyError(f"Key '{new_key}' does not exist in default preferences.")
                new_current = new_current[new_key_part] if isinstance(new_current, dict) else {}

            # Set the new key path in updated_prefs
            new_current = updated_prefs
            for new_key_part in new_keys[:-1]:
                new_current = new_current.setdefault(new_key_part, {})
            new_current[new_keys[-1]] = value

    return updated_prefs


def prune_unused_preferences(user_prefs: dict, default_prefs: dict) -> dict:
    """Delete keys in user preferences that are not in DEFAULT_USER_PREFERENCES.

    Args:
        user_prefs (dict): The users current preferences.
        default_prefs (dict): The default preferences.

    Returns:
        dict: Updated preferences with unused keys deleted.
    """
    updated_prefs = user_prefs.copy()
    keys_to_delete = [key for key in updated_prefs if key not in default_prefs]

    for key in keys_to_delete:
        del updated_prefs[key]

    for key, value in updated_prefs.items():
        if isinstance(value, dict) and isinstance(default_prefs.get(key), dict):
            updated_prefs[key] = prune_unused_preferences(value, default_prefs[key])

    return updated_prefs


def update_preferences(user_prefs: dict, default_prefs: dict, transfer_map: dict | None = None) -> dict:
    """Update user preferences to match DEFAULT_USER_PREFERENCES.

    Args:
        user_prefs (dict): The users current preferences.
        default_prefs (dict): The default preferences.
        transfer_map (dict | None): A mapping of old to new preference keys where their values should be transferred.
        delete_unused (bool): Whether to delete preferences not in DEFAULT_USER_PREFERENCES.

    Returns:
        dict: Updated user preferences.
    """
    updated_prefs = fill_missing_default_preferences(user_prefs, default_prefs)
    if transfer_map:
        updated_prefs = update_preference_keys(updated_prefs, default_prefs, transfer_map)
    updated_prefs = prune_unused_preferences(updated_prefs, default_prefs)
    return updated_prefs


def migrate_preferences(session: Session, default_preferences: dict, transfer_map: dict | None = None) -> None:
    """Migrate user preferences to match DEFAULT_USER_PREFERENCES.

    Args:
        session (Session): SQLAlchemy session.
        transfer_map (dict | None): A mapping of old to new preference keys where their values should be transferred.
        delete_unused (bool): Whether to delete preferences not in DEFAULT_USER_PREFERENCES.
    """
    for user in session.query(models.User).all():
        user.preferences = update_preferences(user.preferences, default_preferences, transfer_map)
        session.add(user)
    session.commit()


if __name__ == "__main__":
    with SessionLocal() as session:
        migrate_preferences(session, default_preferences=DEFAULT_USER_PREFERENCES)
