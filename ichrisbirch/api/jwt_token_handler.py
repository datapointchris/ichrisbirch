import hashlib
import logging
from datetime import timedelta

import jwt
import pendulum
from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch.config import Settings
from ichrisbirch.models import JWTRefreshToken

logger = logging.getLogger(__name__)


def _hash_token(token: str) -> str:
    """Hash a token using SHA-256 for secure storage.

    SHA-256 is appropriate for tokens (vs bcrypt for passwords) because:
    - Tokens are already high-entropy random values
    - Fast verification is needed on every refresh request
    """
    return hashlib.sha256(token.encode()).hexdigest()


class JWTTokenHandler:
    def __init__(
        self,
        settings: Settings,
        session: Session,
        access_token_expire_delta: timedelta | None = None,
        refresh_token_expire_delta: timedelta | None = None,
        secret_key: str | None = None,
        algorithm: str | None = None,
    ):
        self.settings = settings
        self.session = session
        self.secret_key = secret_key or self.settings.auth.jwt_secret_key
        self.algorithm = algorithm or self.settings.auth.jwt_signing_algorithm
        self.access_token_expire_delta = access_token_expire_delta or self.settings.auth.access_token_expire
        self.refresh_token_expire_delta = refresh_token_expire_delta or self.settings.auth.refresh_token_expire

    def _generate_jwt(self, user_id: str, expires_delta: timedelta):
        payload = {'sub': user_id, 'iat': pendulum.now(), 'exp': pendulum.now() + expires_delta}
        token = jwt.encode(payload=payload, key=self.secret_key, algorithm=self.algorithm)
        return token

    def create_access_token(self, user_id: str):
        logger.debug(f'creating access token for user: {user_id}')
        return self._generate_jwt(user_id, expires_delta=self.access_token_expire_delta)

    def create_refresh_token(self, user_id: str):
        logger.debug(f'creating refresh token for user: {user_id}')
        return self._generate_jwt(user_id, expires_delta=self.refresh_token_expire_delta)

    def store_refresh_token(self, user_id: str, refresh_token: str):
        """Store a hashed refresh token for the user."""
        token_hash = _hash_token(refresh_token)
        stmt = select(JWTRefreshToken).where(JWTRefreshToken.user_id == user_id)
        if existing_token := self.session.scalar(stmt):
            existing_token.refresh_token = token_hash
            existing_token.date_stored = pendulum.now()
            logger.debug(f'updating refresh token for user: {user_id}')
        else:
            token = JWTRefreshToken(user_id=user_id, refresh_token=token_hash, date_stored=pendulum.now())
            self.session.add(token)
            logger.debug(f'storing refresh token for user: {user_id}')
        self.session.commit()

    def verify_refresh_token(self, user_id: str, refresh_token: str) -> bool:
        """Verify a refresh token matches the stored hash for the user."""
        stmt = select(JWTRefreshToken).where(JWTRefreshToken.user_id == user_id)
        if stored := self.session.scalar(stmt):
            token_hash = _hash_token(refresh_token)
            if stored.refresh_token == token_hash:
                logger.debug(f'refresh token verified for user: {user_id}')
                return True
            logger.warning(f'refresh token mismatch for user: {user_id}')
            return False
        logger.debug(f'no refresh token found for user: {user_id}')
        return False

    def delete_refresh_token(self, user_id: str):
        self.session.execute(delete(JWTRefreshToken).where(JWTRefreshToken.user_id == user_id))
        self.session.commit()
        logger.debug(f'deleted refresh token for user: {user_id}')
