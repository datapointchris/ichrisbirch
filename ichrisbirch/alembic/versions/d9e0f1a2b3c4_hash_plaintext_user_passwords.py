"""Hash every user password stored as plaintext

`PATCH /users/{id}/` wrote a new password as sent, because the model hashed
only on insert. Each such row holds its plaintext. It also fails every login,
since a value that is not a hash never verifies.

This hashes every password not shaped like a werkzeug hash: a scrypt or pbkdf2
method, then a salt and a digest, joined by `$`. Only those values verify today,
and they are left alone, so no working credential changes. A plaintext row
starts verifying against the password it was set to.

It logs how many rows it hashed, and nothing that names a row.

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
Create Date: 2026-10-08

"""

import logging

import sqlalchemy as sa
from alembic import op
from werkzeug.security import generate_password_hash

revision = 'd9e0f1a2b3c4'
down_revision = 'c8d9e0f1a2b3'
branch_labels = None
depends_on = None

HASH_METHODS = ('scrypt', 'pbkdf2')

logger = logging.getLogger('alembic.runtime.migration')


def is_werkzeug_hash(value: str) -> bool:
    method, _, salt_and_digest = value.partition('$')
    return method.split(':', 1)[0] in HASH_METHODS and '$' in salt_and_digest


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text('SELECT id, password FROM users')).all()
    hashed = [{'id': user_id, 'password': generate_password_hash(password)} for user_id, password in rows if not is_werkzeug_hash(password)]
    if hashed:
        conn.execute(sa.text('UPDATE users SET password = :password WHERE id = :id'), hashed)
    logger.info('Hashed %d plaintext user passwords', len(hashed))


def downgrade() -> None:
    """A hash cannot be turned back into its password, so this changes nothing."""
