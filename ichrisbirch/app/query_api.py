import logging
from typing import Any
from typing import Generic
from typing import TypeVar

import httpx
from flask import flash
from flask_login import current_user
from pydantic import BaseModel

from ichrisbirch import models
from ichrisbirch.app import utils
from ichrisbirch.config import get_settings

settings = get_settings()

ModelType = TypeVar('ModelType', bound=BaseModel)

ServiceUser = models.User(
    name=settings.users.service_account_user_name,
    email=settings.users.service_account_user_email,
    password=settings.users.service_account_user_password,
)


class QueryAPI(Generic[ModelType]):
    """
    user: solely for adding the headers to authenticate with the api
    WARNING: setting the default user to `current_user` causes the API to make hundreds of identical requests.
    """

    def __init__(
        self,
        base_url: str,
        logger: logging.Logger,
        response_model: type[ModelType],
        user: models.User | Any = None,
    ):
        self.base_url = utils.url_builder(settings.api_url, base_url)
        self.logger = logger
        self.response_model = response_model
        self.user = user or (current_user if (current_user and current_user.is_authenticated) else None)

    def _handle_request(self, method: str, endpoint: Any | None = None, **kwargs):
        url = utils.url_builder(self.base_url, endpoint) if endpoint else self.base_url
        headers = {
            'X-User-ID': (self.user.get_id() or '') if self.user else '',
            'X-Application-ID': settings.flask.app_id,
        }
        headers_to_log = {'X-User-ID': headers.get('X-User-ID'), 'X-Application-ID': f'XXXX{settings.flask.app_id[:4]}'}
        kwargs_to_log = ''
        if additional_headers := kwargs.pop('headers', None):
            headers.update(**additional_headers)
            headers_to_log.update(**additional_headers)
        if kwargs:
            if settings.ENVIRONMENT == 'production':
                kwargs_to_log = ', '.join([f'{k}=XXXXXXXX' for k in kwargs.keys()])
            else:
                kwargs_to_log = ', '.join([f'{k}={v}' for k, v in kwargs.items()])
        self.logger.debug(f'{method} {url} headers={headers_to_log}{", " + kwargs_to_log}')
        self.logger.debug(f'current_user={self.user}')
        response = None
        try:
            with httpx.Client() as client:
                response = client.request(method, url, headers=headers, **kwargs, follow_redirects=True)
                response.raise_for_status()
                return response
        except httpx.HTTPError as e:
            error_message = f'Request Error: {e}'
            self.logger.error(error_message)
            flash(error_message, 'error')
            if response:
                self.logger.error(response.text)
                if settings.ENVIRONMENT == 'development':
                    flash(response.text, 'error')
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
