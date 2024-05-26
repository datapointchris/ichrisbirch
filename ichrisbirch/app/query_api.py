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
    """

    def __init__(
        self,
        base_url: str,
        logger: logging.Logger,
        response_model: Type[ModelType],
        user: models.User | Any = current_user,
    ):
        self.base_url = utils.url_builder(settings.api_url, base_url)
        self.logger = logger
        self.response_model = response_model
        self.user = user

    def _handle_request(
        self,
        method: str,
        endpoint: Any | None = None,
        params: dict | None = None,
        data: dict | None = None,
        expected_response_code: int = 200,
    ):
        url = utils.url_builder(self.base_url, endpoint) if endpoint else self.base_url
        self.logger.debug(f'{method} {url} {data if settings.ENVIRONMENT != "production" else ""}')
        headers = {'X-User-ID': self.user.get_id() or '', 'X-Application-ID': settings.flask.app_id}
        response = httpx.request(method, url, follow_redirects=True, params=params, headers=headers, json=data)
        utils.handle_if_not_response_code(expected_response_code, response, self.logger)
        return response

    def get_one(self, endpoint: Any | None = None, params: dict | None = None):
        response = self._handle_request('GET', endpoint, params)
        if exists := response.json():
            return self.response_model(**exists)
        return None

    def get_many(self, endpoint: Any | None = None, params: dict | None = None):
        response = self._handle_request('GET', endpoint, params)
        return [self.response_model(**result) for result in response.json()]

    def post(self, endpoint: Any | None = None, data: dict = {}):
        response = self._handle_request('POST', endpoint, data=data, expected_response_code=201)
        return self.response_model(**response.json())

    def patch(self, endpoint: Any | None = None, data: dict = {}):
        response = self._handle_request('PATCH', endpoint, data=data)
        return self.response_model(**response.json())

    def delete(self, endpoint: Any | None = None):
        return self._handle_request('DELETE', endpoint, expected_response_code=204)
