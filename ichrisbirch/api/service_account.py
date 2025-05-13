import logging
import os
from typing import Callable, Optional

from flask import Flask, current_app
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch.config import get_settings
from ichrisbirch.database.sqlalchemy.session import get_session_factory

logger = logging.getLogger('api.service_account')

# Type for session factory
SessionFactory = Callable[[], Session]


class APIServiceAccount:
    """Service account for API operations that need authentication but aren't triggered by a user."""

    def __init__(self, app: Optional[Flask] = None, session_factory: Optional[SessionFactory] = None, settings_override=None, current_app=None):
        """
        Initialize the service account.
        
        Args:
            app: Flask application instance (optional)
            session_factory: Function that returns a new database session (optional)
            settings_override: Settings object to use instead of global settings (optional)
            current_app: Current Flask application instance (optional)
        """
        self.app = app or current_app
        self._user = None
        self._session_factory = session_factory
        
        # Use provided settings or detect from environment
        if settings_override:
            self._settings = settings_override
        elif current_app and current_app.config.get('TESTING'):
            self._settings = get_settings()
            logger.debug('APIServiceAccount using testing settings from Flask context')
        elif os.environ.get('ENVIRONMENT') == 'testing':
            self._settings = get_settings()
            logger.debug('APIServiceAccount using testing settings from environment')
        else:
            self._settings = get_settings()

    @property
    def session_factory(self) -> SessionFactory:
        """Get the session factory, using the provided one or falling back to the default."""
        if self._session_factory is not None:
            return self._session_factory
        
        # Get the session factory on demand to ensure it uses the current environment
        return get_session_factory()

    def _get_session(self) -> Session:
        """Get a new database session."""
        return self.session_factory()

    def _get_user(self):
        """Retrieve the service account user from the database."""
        with self._get_session() as session:
            q = select(models.User).filter(models.User.email == self._settings.users.service_account_user_email)
            if user := (session.execute(q).scalars().first()):
                logger.debug(f'retrieved service account user: {user.email}')
                self._user = user
            else:
                message = f'could not find service account user: {self._settings.users.service_account_user_email}'
                logger.error(message)
                raise Exception(message)

    @property
    def user(self) -> models.User | None:
        """Get the service account user, retrieving it from the database if needed."""
        if self._user is None:
            self._get_user()
        return self._user
