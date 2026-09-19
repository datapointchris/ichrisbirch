import email.utils
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import Depends
from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ichrisbirch.ai.assistants.anthropic import AssistantOutputError
from ichrisbirch.ai.assistants.anthropic import AssistantUsageLimitReached
from ichrisbirch.api import endpoints
from ichrisbirch.api.article_import_worker import ArticleImportWorker
from ichrisbirch.api.endpoints.auth import get_admin_user
from ichrisbirch.api.endpoints.auth import get_current_user
from ichrisbirch.api.exceptions import FailedDependencyException
from ichrisbirch.api.middleware import ResponseLoggerMiddleware
from ichrisbirch.api.redis_client import get_redis_client
from ichrisbirch.config import Settings
from ichrisbirch.util import log_caller

logger = structlog.get_logger()


async def http_exception_handler_logger(request, exc):
    logger.error('api_http_error', path=request.url.path, error=str(exc))
    return await http_exception_handler(request, exc)


async def request_validation_exception_handler_logger(request, exc):
    logger.error('api_validation_error', path=request.url.path, error=str(exc))
    return await request_validation_exception_handler(request, exc)


async def assistant_output_error_handler(request, exc):
    """Answer an unusable reply as a failed dependency that names why and carries what Claude Code returned.

    The error stays a domain exception until it reaches here, because the bulk
    import worker calls the same helpers and records `str(e)` in a database column
    and a Redis payload, where a transport exception would put the whole reply.
    """
    logger.error('assistant_output_unusable', path=request.url.path, reason=str(exc.reason), error=str(exc))
    detail = {'reason': str(exc.reason), 'message': str(exc), 'raw_assistant_output': exc.raw_output}
    return await http_exception_handler(request, FailedDependencyException(detail))


async def assistant_usage_limit_handler(request, exc):
    """Answer a call refused by the Claude plan's usage limit as a service that will be back.

    `Retry-After` carries the reset time when Claude Code reported one.
    """
    logger.warning('assistant_usage_limit_reached', path=request.url.path, resets_at=exc.resets_at, limit_type=exc.limit_type)
    headers = {'Retry-After': email.utils.format_datetime(exc.resets_at, usegmt=True)} if exc.resets_at else None
    return JSONResponse(status_code=503, content={'detail': str(exc)}, headers=headers)


async def api_exception_handler(request, exc):
    logger.error('api_unhandled_error', path=request.url.path, error=str(exc), error_type=type(exc).__name__)
    return JSONResponse(status_code=500, content={'message': f'Internal server error: {type(exc).__name__}'})


@log_caller
def create_api(settings: Settings) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        redis_client = get_redis_client(settings)
        worker = ArticleImportWorker(redis_client, settings)
        worker.start()
        app.state.settings = settings
        app.state.redis_client = redis_client
        app.state.article_import_worker = worker
        yield
        worker.stop()
        redis_client.close()

    api = FastAPI(title=settings.fastapi.title, description=settings.fastapi.description, lifespan=lifespan)
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

    api.include_router(endpoints.home.router, prefix='', include_in_schema=False)
    api.include_router(endpoints.admin.router, prefix='/admin', dependencies=[Depends(get_admin_user)])
    api.include_router(endpoints.admin.ws_router, prefix='/admin')  # WebSocket handles its own auth
    api.include_router(endpoints.articles.router, prefix='/articles', dependencies=deps)
    api.include_router(endpoints.auth.router, prefix='/auth')
    api.include_router(endpoints.autofun.router, prefix='/autofun', dependencies=deps)
    api.include_router(endpoints.autotasks.router, prefix='/autotasks', dependencies=deps)
    api.include_router(endpoints.books.router, prefix='/books', dependencies=deps)
    api.include_router(endpoints.coffee.shops_router, prefix='/coffee/shops', dependencies=deps)
    api.include_router(endpoints.coffee.beans_router, prefix='/coffee/beans', dependencies=deps)
    api.include_router(endpoints.box_packing.router, prefix='/box-packing', dependencies=deps)
    api.include_router(endpoints.countdowns.router, prefix='/countdowns', dependencies=deps)
    api.include_router(endpoints.durations.router, prefix='/durations', dependencies=deps)
    api.include_router(endpoints.patterns.router, prefix='/patterns', dependencies=deps)
    api.include_router(endpoints.events.router, prefix='/events', dependencies=deps)
    api.include_router(endpoints.github_issues.router, prefix='/github/issues', dependencies=deps)
    api.include_router(endpoints.habits.router, prefix='/habits', dependencies=deps)
    api.include_router(endpoints.money_wasted.router, prefix='/money-wasted', dependencies=deps)
    api.include_router(endpoints.personal_api_keys.router, prefix='/api-keys', dependencies=deps)
    api.include_router(endpoints.projects.router, prefix='/projects', dependencies=deps)
    api.include_router(endpoints.project_items.router, prefix='/project-items', dependencies=deps)
    api.include_router(endpoints.project_item_tasks.router, prefix='/project-items/{item_id}/tasks', dependencies=deps)
    api.include_router(endpoints.recipes.router, prefix='/recipes', dependencies=deps)
    api.include_router(endpoints.server.router, prefix='/server', dependencies=deps)
    api.include_router(endpoints.strains.router, prefix='/strains', dependencies=deps)
    api.include_router(endpoints.tasks.router, prefix='/tasks', dependencies=deps)
    api.include_router(endpoints.users.router, prefix='/users')
    logger.info('routers_registered')

    api.add_exception_handler(HTTPException, http_exception_handler_logger)
    api.add_exception_handler(RequestValidationError, request_validation_exception_handler_logger)
    api.add_exception_handler(AssistantOutputError, assistant_output_error_handler)
    api.add_exception_handler(AssistantUsageLimitReached, assistant_usage_limit_handler)
    api.add_exception_handler(Exception, api_exception_handler)
    logger.info('exception_handlers_registered')

    logger.info('api_initialized')
    return api
