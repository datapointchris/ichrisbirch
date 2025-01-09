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
from sqlalchemy_json import mutable_json_type
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from ichrisbirch.database.sqlalchemy.base import Base

MutableJSONB = mutable_json_type(dbtype=JSONB, nested=True)

DEFAULT_USER_PREFERENCES = {
    'theme': 'turquoise',
    'dark_mode': True,
    'notifications': False,
    'box_packing': {
        'compact_view': True,
    },
    'dashboard_layout': [
        ['tasks_priority', 'countdowns', 'events'],
        ['habits', 'brainlog', 'devlog'],
    ],
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
