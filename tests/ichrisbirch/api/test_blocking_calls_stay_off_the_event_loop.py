"""FastAPI runs an `async def` handler on the event loop, so blocking work in one
holds every other request in the worker until it returns."""

import ast
import inspect
import textwrap
from pathlib import Path

from fastapi.routing import APIRoute

import ichrisbirch

PACKAGE = Path(ichrisbirch.__file__).parent
AWAITING_NODES = (ast.Await, ast.AsyncFor, ast.AsyncWith)

Function = ast.FunctionDef | ast.AsyncFunctionDef


def awaits(function) -> bool:
    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    return any(isinstance(node, AWAITING_NODES) for node in ast.walk(tree))


def called_names(node: ast.AST) -> set[str]:
    names = set()
    for call in ast.walk(node):
        if isinstance(call, ast.Call):
            if isinstance(call.func, ast.Name):
                names.add(call.func.id)
            elif isinstance(call.func, ast.Attribute):
                names.add(call.func.attr)
    return names


def package_functions() -> list[tuple[Path, Function]]:
    return [(path, node) for path in PACKAGE.rglob('*.py') for node in ast.walk(ast.parse(path.read_text())) if isinstance(node, Function)]


def page_fetchers(functions: list[tuple[Path, Function]]) -> set[str]:
    """`get_page` and every function that calls it or calls one that does, by name.

    A function handed to `run_in_threadpool` is an argument rather than a call,
    so the caller does not join the set.
    """
    calls: dict[str, set[str]] = {}
    for _, node in functions:
        calls.setdefault(node.name, set()).update(called_names(node))
    reached = {'get_page'}
    while new := {name for name, callees in calls.items() if callees & reached} - reached:
        reached |= new
    return reached


def test_an_async_handler_awaits_something(test_api):
    idle = sorted(
        f'{",".join(sorted(route.methods))} {route.path}'
        for route in test_api.app.routes
        if isinstance(route, APIRoute) and inspect.iscoroutinefunction(route.endpoint) and not awaits(route.endpoint)
    )
    assert idle == [], 'these await nothing, so they block the event loop: make them def'


def test_no_async_function_fetches_a_page_on_the_event_loop():
    """A page fetch takes seconds, and one in an async handler that also awaits
    the assistant passes the test above."""
    functions = package_functions()
    fetchers = page_fetchers(functions)
    assert {'get_page', 'read_article_page'} <= fetchers, 'the walk no longer finds the fetchers it exists for'

    blocking = sorted(
        f'{path.relative_to(PACKAGE.parent)}:{node.lineno} {node.name} calls {", ".join(sorted(called_names(node) & fetchers))}'
        for path, node in functions
        if isinstance(node, ast.AsyncFunctionDef) and called_names(node) & fetchers
    )
    assert blocking == [], 'pass these to run_in_threadpool rather than calling them'
