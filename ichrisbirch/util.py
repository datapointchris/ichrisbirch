import functools
import inspect
import logging
from pathlib import Path

logger = logging.getLogger('util')


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
    return find_project_root(parent_directory, target_file)


def get_logger_filename_from_handlername(handler_name: str) -> str | None:
    if handler := logging.getHandlerByName(handler_name):
        if isinstance(handler, logging.FileHandler):
            return Path(handler.baseFilename).name
    return None


def log_caller(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        current_frame = inspect.currentframe()
        caller_frame = current_frame.f_back
        caller_name = caller_frame.f_code.co_name
        caller_file = caller_frame.f_code.co_filename
        truncated_file = '/'.join(caller_file.split('/')[5:])
        logger.info(f"function '{func.__name__}' was called by '{caller_name}' in {truncated_file}")
        return func(*args, **kwargs)

    return wrapper
