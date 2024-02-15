import pathlib

import httpx
from fastapi import status


def show_status_and_response(response: httpx.Response) -> dict[str, str]:
    """Convert status code to description and return response if any"""
    d = {}
    for attr in dir(status):
        code = attr.split('_')[1]
        d[int(code)] = attr
    try:
        content = response.json()
    except (httpx.DecodingError, TypeError):
        content = '<no response content>'

    return {d.get(response.status_code, 'UNKNOWN'): content}


def find_project_root(
    directory: pathlib.Path = pathlib.Path.cwd(),
    target_file: str = 'pyproject.toml',
) -> pathlib.Path:
    """Find the project root directory"""
    for file in directory.iterdir():
        if file.name == target_file:
            return directory.absolute()
    parent_directory = directory.parent
    if parent_directory == directory:
        raise FileNotFoundError(f'Could not find project root directory searching for {target_file}')
    return find_project_root(parent_directory)
