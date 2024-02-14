import logging

import requests
from flask import abort, flash


def handle_if_not_response_code(response_code: int, response: requests.Response, logger: logging.Logger):
    '''Flash and log an error if the response status code is not the expected response code.

    Logger needs to be passed in as a parameter, or all logging is logged from the helpers file
    '''
    if response.status_code != response_code:
        error_message = f'{response.url} : {response.status_code} {response.reason}'
        logger.error(error_message)
        logger.error(response.text)
        flash(error_message, 'error')
        flash(response.text, 'error')
        abort_message = f'Expected {response_code} but received {response.status_code}, check logs for details'
        abort(502, {'abort_message': abort_message, 'error_message': error_message})
