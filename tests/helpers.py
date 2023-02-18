from typing import Sequence


def format_endpoint(paths: str | int | float | set | Sequence) -> str:
    """Converts string arguments to path with leading and trailing slashes

    Accepts any argument that can be converted to a string

    Ex:

    >>> endpoint(['tasks', 'complete', 3])
    >>> '/tasks/complete/3/'

    >>> endpoint('health')
    >>> '/health/'

    """
    if isinstance(paths, (str, int, float)):
        return f'/{paths}/'

    if isinstance(paths, (set, Sequence)):
        return f'/{"/".join([str(s) for s in paths])}/'
