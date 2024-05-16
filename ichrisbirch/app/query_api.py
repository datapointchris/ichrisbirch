import logging
from typing import Any
from typing import Generic
from typing import Type
from typing import TypeVar

import httpx
from pydantic import BaseModel

from ichrisbirch.app import utils
from ichrisbirch.config import get_settings

settings = get_settings()

ModelType = TypeVar('ModelType', bound=BaseModel)


class QueryAPI(Generic[ModelType]):

    def __init__(self, base_url: str, api_key: str, logger: logging.Logger, response_model: Type[ModelType]):
        self.base_url = utils.url_builder(settings.api_url, base_url)
        self.api_key = api_key
        self.logger = logger
        self.response_model = response_model

    def _handle_request(
        self,
        method: str,
        endpoint: Any | None = None,
        params: dict | None = None,
        data: dict | None = None,
        expected_response_code: int = 200,
    ):
        url = utils.url_builder(self.base_url, endpoint) if endpoint else self.base_url
        self.logger.debug(f'{method} {url} {data=}')
        response = httpx.request(method, url, follow_redirects=True, params=params, json=data)
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
