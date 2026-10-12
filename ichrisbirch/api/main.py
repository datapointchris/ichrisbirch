import email.utils
import re
from collections.abc import AsyncGenerator
from collections.abc import Mapping
from collections.abc import Sequence
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Any

import structlog
from fastapi import APIRouter
from fastapi import Depends
from fastapi import FastAPI
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.utils import is_body_allowed_for_status_code
from starlette.convertors import Convertor
from starlette.convertors import register_url_convertor
from starlette.exceptions import HTTPException
from starlette.responses import Response
from starlette.routing import Match

from ichrisbirch.ai.assistants.anthropic import AssistantOutputError
from ichrisbirch.ai.assistants.anthropic import AssistantUsageLimitReached
from ichrisbirch.api import API_PREFIX
from ichrisbirch.api import endpoints
from ichrisbirch.api.article_import_worker import QUEUE_READ_TIMEOUT_SECONDS
from ichrisbirch.api.article_import_worker import ArticleImportWorker
from ichrisbirch.api.endpoints.auth import get_admin_user
from ichrisbirch.api.endpoints.auth import get_current_user
from ichrisbirch.api.endpoints.auth import get_current_user_or_scoped_client
from ichrisbirch.api.middleware import ResponseLoggerMiddleware
from ichrisbirch.api.protected_resource import add_protected_resource_route
from ichrisbirch.api.redis_client import REQUEST_READ_TIMEOUT_SECONDS
from ichrisbirch.api.redis_client import get_redis_client
from ichrisbirch.config import Settings
from ichrisbirch.util import log_caller

logger = structlog.get_logger()


VALIDATION_SCOPES = ('body', 'query', 'path', 'header', 'cookie')


class RetiredPathConvertor(Convertor[str]):
    """Any path under `/api/` outside the current version, so `/api/v1` keeps its own 404 and 405."""

    regex = rf'(?!{re.escape(API_PREFIX.removeprefix("/api/"))}(?:/|$)).*'

    def convert(self, value: str) -> str:
        return value

    def to_string(self, value: str) -> str:
        return value


register_url_convertor('retired', RetiredPathConvertor())


def retired_path(rest: str):
    """An installed client still calling the unversioned routes reads a 404 as an answer about a row."""
    raise HTTPException(status.HTTP_410_GONE, f'this API serves {API_PREFIX}; update the client calling it')


def error_response(status_code: int, message: str, headers: Mapping[str, str] | None = None, **fields: Any) -> Response:
    """Answer an error as `{"error": <status phrase>, "message": <reason>}`.

    `message` is always a string, so a client reads one field to say what went
    wrong. Anything a caller reads beyond the reason rides beside the two.
    """
    if not is_body_allowed_for_status_code(status_code):
        return Response(status_code=status_code, headers=headers)
    try:
        phrase = HTTPStatus(status_code).phrase
    except ValueError:
        phrase = str(status_code)
    content = {'error': phrase, 'message': message, **jsonable_encoder(fields)}
    return JSONResponse(status_code=status_code, content=content, headers=headers)


def validation_message(errors: Sequence[dict[str, Any]]) -> str:
    """Each refused field as `field: reason`, the field dotted below the part of the request it came in."""
    parts = []
    for error in errors:
        loc = [str(segment) for segment in error.get('loc', ())]
        if loc and loc[0] in VALIDATION_SCOPES:
            loc = loc[1:]
        field = '.'.join(loc)
        parts.append(f'{field}: {error["msg"]}' if field else error['msg'])
    return '; '.join(parts)


async def http_exception_handler_logger(request, exc):
    """A dict detail carries its reason under `message`, and each other key becomes a field beside it."""
    logger.error('api_http_error', path=request.url.path, error=str(exc))
    if isinstance(exc.detail, dict):
        fields = dict(exc.detail)
        return error_response(exc.status_code, str(fields.pop('message', '')), exc.headers, **fields)
    # The router's own 404 and 405 carry only the status phrase, so these name the path instead.
    if exc.status_code == status.HTTP_404_NOT_FOUND and exc.detail == HTTPStatus.NOT_FOUND.phrase:
        return error_response(exc.status_code, f'no route answers {request.url.path}', exc.headers)
    if exc.status_code == status.HTTP_405_METHOD_NOT_ALLOWED and exc.detail == HTTPStatus.METHOD_NOT_ALLOWED.phrase:
        allow = allowed_methods(request)
        headers = {**(exc.headers or {}), 'Allow': allow}
        return error_response(exc.status_code, f'{request.url.path} takes {allow}, not {request.method}', headers)
    return error_response(exc.status_code, str(exc.detail), exc.headers)


def allowed_methods(request) -> str:
    """Every method a route on this path takes.

    Each method is a route of its own here, and Starlette's `Allow` names only
    the first one that matched the path.
    """
    methods: set[str] = set()
    for route in request.app.routes:
        match, _ = route.matches(request.scope)
        if match != Match.NONE:
            methods.update(getattr(route, 'methods', None) or ())
    return ', '.join(sorted(methods))


async def request_validation_exception_handler_logger(request, exc):
    """`errors` keeps FastAPI's list, which the Vue app reads to mark each refused field."""
    logger.error('api_validation_error', path=request.url.path, error=str(exc))
    errors = jsonable_encoder(exc.errors())
    return error_response(status.HTTP_422_UNPROCESSABLE_CONTENT, validation_message(errors), errors=errors)


async def assistant_output_error_handler(request, exc):
    """Answer an unusable reply as a failed dependency that names why and carries what Claude Code returned.

    The error stays a domain exception until it reaches here, because the bulk
    import worker calls the same helpers and records `str(e)` in a database column
    and a Redis payload, where a transport exception would put the whole reply.
    The status is 424 for the reason `FailedDependencyException` gives.
    """
    logger.error('assistant_output_unusable', path=request.url.path, reason=str(exc.reason), error=str(exc))
    return error_response(status.HTTP_424_FAILED_DEPENDENCY, str(exc), reason=str(exc.reason), raw_assistant_output=exc.raw_output)


async def assistant_usage_limit_handler(request, exc):
    """Answer a call refused by the Claude plan's usage limit as a service that will be back.

    `Retry-After` carries the reset time when Claude Code reported one.
    """
    logger.warning('assistant_usage_limit_reached', path=request.url.path, resets_at=exc.resets_at, limit_type=exc.limit_type)
    headers = {'Retry-After': email.utils.format_datetime(exc.resets_at, usegmt=True)} if exc.resets_at else None
    return error_response(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc), headers)


async def api_exception_handler(request, exc):
    logger.error('api_unhandled_error', path=request.url.path, error=str(exc), error_type=type(exc).__name__)
    return error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, f'Internal server error: {type(exc).__name__}')


@log_caller
def create_api(settings: Settings) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        request_redis = get_redis_client(settings, read_timeout=REQUEST_READ_TIMEOUT_SECONDS)
        worker_redis = get_redis_client(settings, read_timeout=QUEUE_READ_TIMEOUT_SECONDS)
        worker = ArticleImportWorker(worker_redis, settings)
        worker.start()
        app.state.settings = settings
        app.state.redis_client = request_redis
        app.state.article_import_worker = worker
        yield
        worker.stop()
        worker_redis.close()
        request_redis.close()

    api = FastAPI(
        title=settings.fastapi.title,
        description=settings.fastapi.description,
        lifespan=lifespan,
        docs_url=f'{API_PREFIX}/docs',
        redoc_url=f'{API_PREFIX}/redoc',
        openapi_url=f'{API_PREFIX}/openapi.json',
    )
    logger.info('api_initializing')
    logger.info('settings_loaded', settings_type=type(settings).__name__)
    logger.debug('api_config', api_url=settings.api_url)
    logger.debug('postgres_config', port=settings.postgres.port, uri=settings.postgres.db_uri)
    logger.debug('sqlalchemy_config', port=settings.sqlalchemy.port, uri=settings.sqlalchemy.db_uri)

    api.add_middleware(ResponseLoggerMiddleware)
    logger.info('middleware_added', middleware='ResponseLoggerMiddleware')

    api.add_middleware(
        CORSMiddleware,
        allow_origins=settings.fastapi.allowed_origins,
        allow_credentials=True,
        allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
        allow_headers=['Authorization', 'Content-Type', 'Accept', 'X-Request-ID', 'X-Application-ID', 'X-User-ID', 'X-Service-Key'],
    )
    logger.info('middleware_added', middleware='CORSMiddleware')

    deps = [Depends(get_current_user)]
    # A route listed in `client_scopes.SCOPE_ROUTES` still answers a scoped client 403 unless its router takes these.
    scoped_deps = [Depends(get_current_user_or_scoped_client)]

    v1 = APIRouter(prefix=API_PREFIX)
    v1.include_router(endpoints.admin.router, prefix='/admin', dependencies=[Depends(get_admin_user)])
    v1.include_router(endpoints.articles.router, prefix='/articles', dependencies=deps)
    v1.include_router(endpoints.autofun.router, prefix='/autofun', dependencies=deps)
    v1.include_router(endpoints.autotasks.router, prefix='/autotasks', dependencies=deps)
    v1.include_router(endpoints.books.router, prefix='/books', dependencies=deps)
    v1.include_router(endpoints.coffee.shops_router, prefix='/coffee/shops', dependencies=deps)
    v1.include_router(endpoints.coffee.beans_router, prefix='/coffee/beans', dependencies=deps)
    v1.include_router(endpoints.box_packing.router, prefix='/box-packing', dependencies=deps)
    v1.include_router(endpoints.countdowns.router, prefix='/countdowns', dependencies=deps)
    v1.include_router(endpoints.durations.router, prefix='/durations', dependencies=deps)
    v1.include_router(endpoints.patterns.router, prefix='/patterns', dependencies=deps)
    v1.include_router(endpoints.events.router, prefix='/events', dependencies=deps)
    v1.include_router(endpoints.habits.router, prefix='/habits', dependencies=deps)
    # Ahead of /issues, whose /{id}/ would otherwise read "initiatives" as an issue.
    v1.include_router(endpoints.issue_initiatives.router, prefix='/issues/initiatives', dependencies=scoped_deps)
    v1.include_router(endpoints.issue_labels.router, prefix='/issues/labels', dependencies=deps)
    v1.include_router(endpoints.issues.router, prefix='/issues', dependencies=scoped_deps)
    v1.include_router(endpoints.money_wasted.router, prefix='/money-wasted', dependencies=deps)
    v1.include_router(endpoints.projects.router, prefix='/projects', dependencies=scoped_deps)
    v1.include_router(endpoints.project_items.router, prefix='/project-items', dependencies=scoped_deps)
    v1.include_router(endpoints.project_item_tasks.router, prefix='/project-items/{item_id}/tasks', dependencies=scoped_deps)
    v1.include_router(endpoints.recipes.router, prefix='/recipes', dependencies=deps)
    v1.include_router(endpoints.server.router, prefix='/server', dependencies=deps)
    v1.include_router(endpoints.shopping.router, prefix='/shopping', dependencies=deps)
    v1.include_router(endpoints.strains.router, prefix='/strains', dependencies=deps)
    v1.include_router(endpoints.tasks.router, prefix='/tasks', dependencies=deps)
    v1.include_router(endpoints.users.router, prefix='/users')
    api.include_router(endpoints.home.router, include_in_schema=False)
    api.include_router(v1)
    api.add_api_route(
        '/api/{rest:retired}', retired_path, methods=['GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE'], include_in_schema=False
    )
    if settings.fastapi.public_url:
        add_protected_resource_route(api, settings.fastapi.public_url, settings.oidc.issuer)
    logger.info('routers_registered')

    api.add_exception_handler(HTTPException, http_exception_handler_logger)
    api.add_exception_handler(RequestValidationError, request_validation_exception_handler_logger)
    api.add_exception_handler(AssistantOutputError, assistant_output_error_handler)
    api.add_exception_handler(AssistantUsageLimitReached, assistant_usage_limit_handler)
    api.add_exception_handler(Exception, api_exception_handler)
    logger.info('exception_handlers_registered')

    logger.info('api_initialized')
    return api
