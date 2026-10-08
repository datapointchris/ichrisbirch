"""FastAPI runs an `async def` handler or dependency on the event loop, so blocking
work in one holds every other request in the worker until it returns."""

import ast
import asyncio
import inspect
import textwrap
import threading
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute

import ichrisbirch

PACKAGE = Path(ichrisbirch.__file__).parent
AWAITING_NODES = (ast.Await, ast.AsyncFor, ast.AsyncWith)

# get_page is the one sanctioned page fetch, and these are the calls that leave
# the process without it: the two YouTube clients and the OIDC key lookups.
OUTBOUND_CALLS = {'get_page', 'YoutubeDL', 'YouTubeTranscriptApi', 'discover_jwks_uri', 'get_signing_key_from_jwt'}

Function = ast.FunctionDef | ast.AsyncFunctionDef


def awaits(function) -> bool:
    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    return any(isinstance(node, AWAITING_NODES) for node in ast.walk(tree))


def async_callables(dependant: Dependant) -> Iterator:
    if dependant.call is not None and inspect.iscoroutinefunction(dependant.call):
        yield dependant.call
    for dependency in dependant.dependencies:
        yield from async_callables(dependency)


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


def outbound_callers(functions: list[tuple[Path, Function]]) -> set[str]:
    """`OUTBOUND_CALLS` and every function that calls one or calls one that does, by name.

    A function handed to `run_in_threadpool` is an argument rather than a call,
    so the caller does not join the set.
    """
    calls: dict[str, set[str]] = {}
    for _, node in functions:
        calls.setdefault(node.name, set()).update(called_names(node))
    reached = set(OUTBOUND_CALLS)
    while new := {name for name, callees in calls.items() if callees & reached} - reached:
        reached |= new
    return reached


def test_an_async_handler_or_dependency_awaits_something(test_api):
    idle = sorted(
        {
            f'{call.__module__}.{call.__qualname__}'
            for route in test_api.app.routes
            if isinstance(route, APIRoute)
            for call in async_callables(route.dependant)
            if not awaits(call)
        }
    )
    assert idle == [], 'these await nothing, so they block the event loop: make them def'


def test_no_async_function_makes_an_outbound_call_on_the_event_loop():
    """A fetch takes seconds, and one in an async handler that also awaits the
    assistant passes the test above."""
    functions = package_functions()
    callers = outbound_callers(functions)
    fetchers = {'read_article_page', 'get_youtube_video_metadata', 'get_youtube_video_text_captions'}
    assert fetchers <= callers, 'a fetcher fell out of the walk, so one of OUTBOUND_CALLS was renamed'

    blocking = sorted(
        f'{path.relative_to(PACKAGE.parent)}:{node.lineno} {node.name} calls {", ".join(sorted(called_names(node) & callers))}'
        for path, node in functions
        if isinstance(node, ast.AsyncFunctionDef) and called_names(node) & callers
    )
    assert blocking == [], 'pass these to run_in_threadpool rather than calling them'


HOLD_SECONDS = 5

# The token request runs the whole login chain, which the admin client overrides.
HELD_CALLS = [
    pytest.param(
        'ichrisbirch.api.endpoints.articles.read_article_page',
        'POST',
        '/articles/create-from-url/',
        {'json': {'url': 'https://held.example/article'}},
        'test_api_logged_in_admin',
        id='article-from-url',
    ),
    pytest.param(
        'ichrisbirch.api.endpoints.books.get_page',
        'POST',
        '/books/goodreads/',
        {'json': {'isbn': '9780000000002'}},
        'test_api_logged_in_admin',
        id='goodreads',
    ),
    pytest.param('docker.from_env', 'GET', '/admin/system/health/', {}, 'test_api_logged_in_admin', id='admin-health'),
    pytest.param(
        'ichrisbirch.api.endpoints.auth.validate_password',
        'POST',
        '/auth/token/',
        {'data': {'username': 'testloginregular@testuser.com', 'password': 'held'}},
        'test_api',
        id='password-login',
    ),
]


@pytest.mark.parametrize(('target', 'method', 'path', 'request_kwargs', 'client_fixture'), HELD_CALLS)
def test_a_held_call_leaves_the_worker_answering(request, monkeypatch, target, method, path, request_kwargs, client_fixture):
    """Every request here shares one event loop, as they do in a uvicorn worker.
    The held call returns early only if `/health` answered while it was held."""
    app = request.getfixturevalue(client_fixture).app
    entered = threading.Event()
    release = threading.Event()
    released_by_the_test = []

    def held(*args, **kwargs):
        entered.set()
        released_by_the_test.append(release.wait(timeout=HOLD_SECONDS))
        raise ConnectionError('held call released')

    monkeypatch.setattr(target, held)

    async def hold_one_and_ask_for_health() -> httpx.Response:
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
            slow = asyncio.create_task(client.request(method, path, **request_kwargs))
            assert await asyncio.to_thread(entered.wait, HOLD_SECONDS), f'{path} never reached {target}'
            health = await client.get('/health')
            release.set()
            await slow
            return health

    health = asyncio.run(hold_one_and_ask_for_health())
    assert health.status_code == 200
    assert released_by_the_test == [True], f'/health waited for {target} to time out, so {path} held the event loop'
