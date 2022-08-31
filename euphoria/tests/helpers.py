def endpoint(*paths: str | list | int) -> str:
    """Converts string arguments to path with leading and trailing slashes

    Accepts any argument that can be converted to a string

    Ex:

    >>> endpoint('tasks', 'complete', 3)
    >>> '/tasks/complete/3/'

    >>> endpoint('health')
    >>> '/health/'

    """
    paths = [paths] if isinstance(paths, str) else paths
    return f'/{"/".join([str(s) for s in paths])}/'
