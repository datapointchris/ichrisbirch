import enum
import random
from datetime import datetime
from typing import Any

from flask_login import UserMixin
from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import validates
from sqlalchemy_json import mutable_json_type
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from ichrisbirch.database.sqlalchemy.base import Base

MutableJSONB = mutable_json_type(dbtype=JSONB, nested=True)


class AppView(enum.StrEnum):
    BLOCK = 'block'
    COMPACT = 'compact'


class ThemeColor(enum.StrEnum):
    TURQUOISE = 'turquoise'
    BLUE = 'blue'
    GREEN = 'green'
    ORANGE = 'orange'
    RED = 'red'
    PURPLE = 'purple'
    YELLOW = 'yellow'
    PINK = 'pink'
    RANDOM = 'random'


PREFERENCE_VALUE_CHECKS = {'view_type': AppView, 'theme_color': ThemeColor}

DEFAULT_USER_PREFERENCES = {
    'theme_color': ThemeColor.TURQUOISE,
    'dark_mode': True,
    'notifications': False,
    'dashboard_layout': [
        ['tasks_priority', 'countdowns', 'events'],
        ['habits', 'brainlog', 'devlog'],
    ],
    'box_packing': {
        'pages': {
            'all': {'view_type': AppView.BLOCK},
            'index': {'view_type': AppView.BLOCK},
            'edit': {'view_type': AppView.BLOCK},
            'orphans': {'view_type': AppView.BLOCK},
            'search': {'view_type': AppView.BLOCK},
        },
    },
    'tasks': {
        'pages': {
            'index': {'view_type': AppView.COMPACT},
            'todo': {'view_type': AppView.COMPACT},
            'completed': {'view_type': AppView.COMPACT},
            'search': {'view_type': AppView.COMPACT},
        },
    },
    'events': {
        'pages': {
            'index': {'view_type': AppView.COMPACT},
        },
    },
}


class User(UserMixin, Base):
    __tablename__ = 'users'

    @staticmethod
    def generate_63_bit_int():
        """Generate a 63-bit integer to use as alternative_id.

        63 bits to ensure it will fit inside Postgres BigInt column
        """
        return random.getrandbits(63)

    @staticmethod
    def default_preferences():
        return DEFAULT_USER_PREFERENCES

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alternative_id: Mapped[int] = mapped_column(BigInteger, unique=True, default=generate_63_bit_int)
    name: Mapped[str] = mapped_column(String(100), unique=False, nullable=False)
    email: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(200), primary_key=False, unique=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, primary_key=False, unique=False, nullable=False, default=False)
    created_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    preferences: Mapped[Any] = mapped_column(MutableJSONB, index=False, unique=False, default=default_preferences)

    @staticmethod
    def _hash_password(mapper, connection, target):
        """The mapper and connection parameters are part of SQLAlchemy's event API. This method is being used as a
        listener function, which is a special kind of function that gets called when a certain event happens. In this
        case, the event is 'before_insert' on the User model.

        mapper:
            This is the Mapper that is handling the operation.
            In SQLAlchemy, a Mapper is the component that links a Python class (in this case, User) to a database table.
            It's responsible for loading objects from the database and saving them back.

        connection:
            This is the Connection being used to communicate with the database.
            It provides a source of database connectivity and behavior.

        target:
            This is the specific instance of the mapped class (in this case, User) that the event is being performed on.
        """
        target.password = generate_password_hash(target.password)

    def _validate_preferences(self, updated_preferences: dict, preferences=DEFAULT_USER_PREFERENCES):
        """Validate if the preference exists and the value is valid."""
        for key, value in updated_preferences.items():
            if key not in preferences:
                raise ValueError(f"Invalid preference: '{key}'. Expected one of {list(preferences.keys())}.")

            current_pref = preferences[key]
            if isinstance(current_pref, dict) and isinstance(value, dict):
                # Recurse into nested dictionaries
                self._validate_preferences(value, current_pref)
            elif key in PREFERENCE_VALUE_CHECKS:
                # Check if this key needs validation against an enum
                enum_class = PREFERENCE_VALUE_CHECKS[key]
                valid_values = [e.value for e in enum_class]
                if value not in valid_values:
                    raise ValueError(f"Invalid value for '{key}'. Expected one of {valid_values}, got '{value}'.")

        return updated_preferences

    @validates('preferences')
    def validate_preferences(self, key, updated_preferences: dict):
        """Validate preferences before setting them.

        Must use secondary private method to avoid recursively calling the validates decorator, which will reset the
        preferences and check for sub preferences at top level.
        """
        return self._validate_preferences(updated_preferences)

    @staticmethod
    def dot_preference_to_nested_dict(dot_key: str, value: Any) -> dict:
        """Create a nested dictionary from a dot-separated key.

        Args:
            dot_key (str): The dot-separated key.
            value (Any): The value to set.

        Returns:
            dict: A nested dictionary representing the dot-separated key.

        Example:
            ```
            dot_key = "tasks.pages.index.view_type"
            value = "grid"
            result = _convert_dot_separated_prefernce_to_nested_dict(dot_key, value)
            print(result)
            >>> {'tasks': {'pages': {'index': {'view_type': 'grid'}}}}
            ```
        """
        if not dot_key:
            return {}
        keys = dot_key.split('.')
        nested_dict = value
        for key in reversed(keys):
            nested_dict = {key: nested_dict}
        return nested_dict

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return self.is_active

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        """Return the alternative_id to keep primary id consistent upon session invalidation."""
        return str(self.alternative_id)

    def set_alternative_id(self):
        """Set alternative_id as 64-bit integer."""
        self.alternative_id = self.generate_63_bit_int()

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'User(name={self.name}, email={self.email}, created_on={self.created_on}, last_login={self.last_login})'


# Associate the listener function with User model, before_insert event
# This will hash the user's password before inserting into the database,
# but not re-hash it any other time, perfect.
event.listen(User, 'before_insert', User._hash_password)
