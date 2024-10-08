from ichrisbirch.config import get_settings

settings = get_settings()


def url_builder(base_url: str, *parts) -> str:
    """Build a URL from a base URL and parts, will always include the trailing slash.

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


def convert_bytes(num: int | float) -> str:
    """Convert bytes to human readable format."""
    for unit in ('B', 'KB', 'MB', 'GB', 'TB', 'PB'):
        if num < 1024.0 or unit == 'PB':
            break
        num /= 1024.0
    return f'{num:.2f} {unit}'
