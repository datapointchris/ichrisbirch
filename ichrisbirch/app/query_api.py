import logging
from typing import Any
from typing import Generic
from typing import Type
from typing import TypeVar

import httpx
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
        response_model: Type[ModelType],
        user: models.User | Any = None,
    ):
        self.base_url = utils.url_builder(settings.api_url, base_url)
        self.logger = logger
        self.response_model = response_model
        self.user = user or (current_user if (current_user and current_user.is_authenticated) else None)

    def _handle_request(self, method: str, endpoint: Any | None = None, expected_response_code: int = 200, **kwargs):
        url = utils.url_builder(self.base_url, endpoint) if endpoint else self.base_url
        headers = {
            'X-User-ID': (self.user.get_id() or '') if self.user else '',
            'X-Application-ID': settings.flask.app_id,
        }
        headers_to_log = {'X-User-ID': headers.get('X-User-ID'), 'X-Application-ID': 'XXXXXXXX'}
        kwargs_to_log = ''
        if additional_headers := kwargs.pop('headers', None):
            headers.update(**additional_headers)
            headers_to_log.update(**additional_headers)
        if kwargs:
            if settings.ENVIRONMENT == 'production':
                kwargs_to_log = ', '.join([f'{k}=XXXXXXXX' for k in kwargs.keys()])
            else:
                kwargs_to_log = ', '.join([f'{k}={v}' for k, v in kwargs.items()])
        self.logger.debug(f'{method} {url} headers={headers_to_log}{", " + kwargs_to_log if kwargs_to_log else ""}')
        self.logger.debug(f'current_user={self.user}')
        response = httpx.request(method, url, follow_redirects=True, **kwargs)
        utils.handle_if_not_response_code(expected_response_code, response, self.logger)
        return response

    def get_one(self, endpoint: Any | None = None, **kwargs) -> ModelType | None:
        response = self._handle_request('GET', endpoint, **kwargs)
        if exists := response.json():
            return self.response_model(**exists)
        return None

    def get_many(self, endpoint: Any | None = None, **kwargs) -> list[ModelType]:
        response = self._handle_request('GET', endpoint, **kwargs)
        return [self.response_model(**result) for result in response.json()]

    def post(self, endpoint: Any | None = None, **kwargs):
        response = self._handle_request('POST', endpoint, **kwargs, expected_response_code=201)
        return self.response_model(**response.json())

    def post_action(self, endpoint: Any | None = None, **kwargs):
        return self._handle_request('POST', endpoint, **kwargs, expected_response_code=200)

    def patch(self, endpoint: Any | None = None, **kwargs):
        response = self._handle_request('PATCH', endpoint, **kwargs)
        return self.response_model(**response.json())

    def delete(self, endpoint: Any | None = None, **kwargs):
        return self._handle_request('DELETE', endpoint, **kwargs, expected_response_code=204)
