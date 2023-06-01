from flask import flash
from requests import Response
import logging

logger = logging.getLogger(__name__)


def validate_response(response: Response) -> bool:
    if response.status_code != 200:
        error_message = f'{response.url} : {response.status_code} {response.reason}'
        logger.error(error_message)
        flash(error_message, 'error')
        return False
    return True
