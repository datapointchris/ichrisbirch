"""FastAPI runs an `async def` handler on the event loop, so one calling the
synchronous session holds every other request in the worker until it returns."""

import ast
import inspect
import textwrap

from fastapi.routing import APIRoute

AWAITING_NODES = (ast.Await, ast.AsyncFor, ast.AsyncWith)


def awaits(function) -> bool:
    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    return any(isinstance(node, AWAITING_NODES) for node in ast.walk(tree))


def test_an_async_handler_awaits_something(test_api):
    idle = sorted(
        f'{",".join(sorted(route.methods))} {route.path}'
        for route in test_api.app.routes
        if isinstance(route, APIRoute) and inspect.iscoroutinefunction(route.endpoint) and not awaits(route.endpoint)
    )
    assert idle == [], 'these await nothing, so they block the event loop: make them def'
