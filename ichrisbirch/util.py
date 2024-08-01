import logging
from pathlib import Path


def find_project_root(
    directory: Path = Path.cwd(),
    target_file: str = 'pyproject.toml',
) -> Path:
    """Find the project root directory based on `target_file`"""
    for file in directory.iterdir():
        if file.name == target_file:
            return directory.absolute()
    parent_directory = directory.parent
    if parent_directory == directory:
        raise FileNotFoundError(f'Could not find project root directory searching for {target_file}')
    return find_project_root(parent_directory)


def get_logger_filename_from_handlername(handler_name: str = 'ichrisbirch_file') -> str | None:
    if handler := logging.getHandlerByName(handler_name):
        if isinstance(handler, logging.FileHandler):
            return handler.baseFilename
    return None
