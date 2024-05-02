import logging
from json.decoder import JSONDecodeError
from typing import Any

import httpx
from flask import abort, flash

from ichrisbirch.config import get_settings

settings = get_settings()


class QueryAPI:

    def __init__(self, base_url: str, api_key: str, logger: logging.Logger, response_model):
        self.base_url = self.url_builder(settings.api_url, base_url)
        self.api_key = api_key
        self.logger = logger
        self.response_model = response_model

    def url_builder(self, base_url, *parts) -> str:
        """Build a URL from a base URL and parts, will always include the trailing slash

        Examples::
            >>> url_builder('http://example.com', 'api', 'v1', 'tasks')
            'http://example.com/api/v1/tasks/'

            >>> url_builder('http://example.com', 'api', 'v1', 'tasks', 1)
            'http://example.com/api/v1/tasks/1/'

            >>> API_URL = 'http://example.com/api/v1'
            >>> url_builder(API_URL, 'tasks')
            'http://example.com/api/v1/tasks/'

        """
        stripped_parts = []
        for part in parts:
            if isinstance(part, (list, tuple, set)):
                stripped_parts.extend([str(p).strip('/') for p in part if str(p).strip('/')])
            elif isinstance(part, str) and part.strip('/'):
                stripped_parts.append(part.strip('/'))
            elif isinstance(part, int):
                stripped_parts.append(str(part))
        return '/'.join([base_url.rstrip('/')] + stripped_parts) + '/'

    def handle_if_not_response_code(self, response_code: int, response: httpx.Response):
        '''Flash and log an error if the response status code is not the expected response code.

        Logger needs to be passed in as a parameter, or all logging is logged from the helpers file
        '''
        if response.status_code != response_code:
            error_message = f'expected {response_code} from {response.url} but received {response.status_code}'
            self.logger.error(error_message)
            self.logger.error(response.text)
            flash(error_message, 'error')
            flash(response.text, 'error')
            abort(502, (f'{error_message}\n{response.text}'))

    def get(self, endpoint: Any | None = None):
        url = self.url_builder(self.base_url, endpoint) if endpoint else self.base_url
        response = httpx.get(url, follow_redirects=True)
        self.handle_if_not_response_code(200, response)
        try:
            return [self.response_model(**result) for result in response.json()]
        except (TypeError, JSONDecodeError):  # Response was only a 200 status code, no data
            return response

    def post(self, endpoint: Any | None = None, data: dict = {}):
        url = self.url_builder(self.base_url, endpoint) if endpoint else self.base_url
        self.logger.debug(f'{data=}')
        response = httpx.post(url, json=data)
        self.handle_if_not_response_code(201, response)
        return self.response_model(**response.json())

    def delete(self, endpoint: Any | None = None):
        url = self.url_builder(self.base_url, endpoint) if endpoint else self.base_url
        response = httpx.delete(url)
        self.handle_if_not_response_code(204, response)
        return response
