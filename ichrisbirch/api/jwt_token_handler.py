import logging
from datetime import timedelta

import jwt
import pendulum
from sqlalchemy import delete
from sqlalchemy import select

from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings
from ichrisbirch.database.sqlalchemy.session import get_session_factory
from ichrisbirch.models import JWTRefreshToken

logger = logging.getLogger('api.token_handler')


class JWTTokenHandler:
    def __init__(
        self,
        settings: Settings | None = None,
        access_token_expire_delta: timedelta | None = None,
        refresh_token_expire_delta: timedelta | None = None,
        secret_key: str | None = None,
        algorithm: str | None = None,
    ):
        self._settings = settings or get_settings()
        self.secret_key = secret_key or self._settings.auth.secret_key
        self.algorithm = algorithm or self._settings.auth.algorithm
        self.access_token_expire_delta = access_token_expire_delta or self._settings.auth.access_token_expire
        self.refresh_token_expire_delta = refresh_token_expire_delta or self._settings.auth.refresh_token_expire

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
        session_factory = get_session_factory()
        with session_factory() as session:
            stmt = select(JWTRefreshToken).where(JWTRefreshToken.user_id == user_id)
            if existing_token := session.scalar(stmt):
                existing_token.refresh_token = refresh_token
                existing_token.date_stored = pendulum.now()
                logger.debug(f'updating refresh token for user: {user_id}')
            else:
                token = JWTRefreshToken(user_id=user_id, refresh_token=refresh_token, date_stored=pendulum.now())
                session.add(token)
                logger.debug(f'storing refresh token for user: {user_id}')
            session.commit()

    def retrieve_refresh_token(self, user_id: str) -> str:
        session_factory = get_session_factory()
        with session_factory() as session:
            stmt = select(JWTRefreshToken).where(JWTRefreshToken.user_id == user_id)
            if token := session.scalar(stmt):
                logger.debug(f'retrieved refresh token for user: {user_id}')
                return token.refresh_token
        logger.debug(f'no refresh token found for user: {user_id}')
        return ''

    def delete_refresh_token(self, user_id: str):
        session_factory = get_session_factory()
        with session_factory() as session:
            session.execute(delete(JWTRefreshToken).where(JWTRefreshToken.user_id == user_id))
            session.commit()
            logger.debug(f'deleted refresh token for user: {user_id}')
