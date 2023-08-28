import logging

import requests
from flask import flash


def log_flash_raise_error(response: requests.Response, logger: logging.Logger):
    error_message = f'{response.url} : {response.status_code} {response.reason}'
    logger.error(error_message)
    logger.error(response.text)
    flash(error_message, 'error')
    flash(response.text, 'error')
    response.raise_for_status()
