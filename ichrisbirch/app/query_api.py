import logging
from typing import Any
from typing import Generic
from typing import TypeVar

import httpx
from flask import session
from flask_login import current_user
from pydantic import BaseModel
from sqlalchemy import select

from ichrisbirch import models
from ichrisbirch.app import utils
from ichrisbirch.config import get_settings
from ichrisbirch.database.sqlalchemy.session import SessionLocal

ModelType = TypeVar('ModelType', bound=BaseModel)
logger = logging.getLogger('app.query_api')


class APIServiceAccount(models.User):
    def __init__(self):
        self.settings = get_settings()
        self.user = None

    def get_user(self):
        with SessionLocal() as session:
            q = select(models.User).filter(models.User.email == self.settings.users.service_account_user_email)
            if user := (session.execute(q).scalars().first()):
                logger.debug(f'retrieved service account user: {user.email}')
                self.user = user
                return user
            else:
                message = f'Coud not find service account user: {self.settings.users.service_account_user_email}'
                logger.error(message)
                raise Exception(message)


class QueryAPI(Generic[ModelType]):
    """
    user: solely for adding the headers to authenticate with the api
    WARNING: setting the default user to `current_user` causes the API to make hundreds of identical requests.
    """

    def __init__(
        self,
        base_url: str,
        response_model: type[ModelType],
        user: models.User | Any = None,
    ):
        self.settings = get_settings()
        self.base_url = utils.url_builder(self.settings.api_url, base_url)
        self.response_model = response_model
        self.user = user or (current_user if (current_user and current_user.is_authenticated) else None)

    def _handle_request(self, method: str, endpoint: Any | None = None, **kwargs):
        url = utils.url_builder(self.base_url, endpoint) if endpoint else self.base_url
        if not self.user:
            user_id = None
            try:
                if user_id := session.get('_user_id'):
                    logger.info('found user id in session')
            except RuntimeError:
                logger.warning('could not access session, outside of request context')
        headers = {
            'X-User-ID': (self.user.get_id() or '') if self.user else user_id,
            'X-Application-ID': self.settings.flask.app_id,
        }
        headers_to_log = {
            'X-User-ID': headers.get('X-User-ID'),
            'X-Application-ID': f'XXXX{self.settings.flask.app_id[:4]}',
        }
        kwargs_to_log = ''
        if additional_headers := kwargs.pop('headers', None):
            headers.update(**additional_headers)
            headers_to_log.update(**additional_headers)
        if kwargs:
            if self.settings.ENVIRONMENT == 'production':
                kwargs_to_log = ', '.join([f'{k}=XXXXXXXX' for k in kwargs.keys()])
            else:
                kwargs_to_log = ', '.join([f'{k}={v}' for k, v in kwargs.items()])
        logger.debug(f'CurrentUser: {self.user.email if self.user else ''}')
        logger.debug(f'{method} {url} headers={headers_to_log}{", " + kwargs_to_log}')
        response = None
        try:
            with httpx.Client() as client:
                return client.request(method, url, headers=headers, **kwargs, follow_redirects=True).raise_for_status()
        except httpx.HTTPError as e:
            logger.error(e)
            if response:
                logger.error(response.text)
            return None

    def get_one(self, endpoint: Any | None = None, **kwargs) -> ModelType | None:
        response = self._handle_request('GET', endpoint, **kwargs)
        if response and response.json():
            return self.response_model(**response.json())
        return None

    def get_many(self, endpoint: Any | None = None, **kwargs) -> list[ModelType]:
        if response := self._handle_request('GET', endpoint, **kwargs):
            return [self.response_model(**result) for result in response.json()]
        return []

    def get_generic(self, endpoint: Any | None = None, **kwargs) -> Any | None:
        """Use this method when the response is not a single ModelType."""
        response = self._handle_request('GET', endpoint, **kwargs)
        if response and response.json():
            return response.json()
        return None

    def post(self, endpoint: Any | None = None, **kwargs):
        if response := self._handle_request('POST', endpoint, **kwargs):
            return self.response_model(**response.json())
        return None

    def post_action(self, endpoint: Any | None = None, **kwargs):
        return self._handle_request('POST', endpoint, **kwargs)

    def patch(self, endpoint: Any | None = None, **kwargs):
        if response := self._handle_request('PATCH', endpoint, **kwargs):
            return self.response_model(**response.json())
        return None

    def delete(self, endpoint: Any | None = None, **kwargs):
        return self._handle_request('DELETE', endpoint, **kwargs)
