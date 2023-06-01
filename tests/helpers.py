from fastapi import status
from requests import JSONDecodeError, Response


def show_status_and_response(response: Response) -> dict:
    """Convert status code to description and return response if any"""
    d = {}
    for attr in dir(status):
        code = attr.split('_')[1]
        d[int(code)] = attr

    try:
        content = response.json()
    except JSONDecodeError:
        content = '<no response content>'

    return {d.get(response.status_code, 'UNKNOWN'): content}
