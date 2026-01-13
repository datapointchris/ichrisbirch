import structlog
from fastapi import Depends
from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ichrisbirch.api import endpoints
from ichrisbirch.api.endpoints.auth import get_admin_user
from ichrisbirch.api.endpoints.auth import get_current_user
from ichrisbirch.api.middleware import ResponseLoggerMiddleware
from ichrisbirch.config import Settings
from ichrisbirch.util import log_caller

logger = structlog.get_logger()


async def http_exception_handler_logger(request, exc):
    logger.error('api_http_error', path=request.url.path, error=str(exc))
    return await http_exception_handler(request, exc)


async def request_validation_exception_handler_logger(request, exc):
    logger.error('api_validation_error', path=request.url.path, error=str(exc))
    return await request_validation_exception_handler(request, exc)


async def api_exception_handler(request, exc):
    logger.error('api_unhandled_error', path=request.url.path, error=str(exc), error_type=type(exc).__name__)
    return JSONResponse(status_code=500, content={'message': f'Internal server error: {type(exc).__name__}'})


@log_caller
def create_api(settings: Settings) -> FastAPI:
    api = FastAPI(title=settings.fastapi.title, description=settings.fastapi.description)
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
        allow_headers=['Authorization', 'Content-Type', 'Accept', 'X-Application-ID', 'X-User-ID', 'X-Service-Key'],
    )
    logger.info('middleware_added', middleware='CORSMiddleware')

    deps = [Depends(get_current_user)]

    api.include_router(endpoints.home.router, prefix='', include_in_schema=False)
    api.include_router(endpoints.admin.router, prefix='/admin', dependencies=[Depends(get_admin_user)])
    api.include_router(endpoints.articles.router, prefix='/articles', dependencies=deps)
    api.include_router(endpoints.auth.router, prefix='/auth')
    api.include_router(endpoints.autotasks.router, prefix='/autotasks', dependencies=deps)
    api.include_router(endpoints.books.router, prefix='/books', dependencies=deps)
    api.include_router(endpoints.box_packing.router, prefix='/box-packing', dependencies=deps)
    api.include_router(endpoints.countdowns.router, prefix='/countdowns', dependencies=deps)
    # Chat routes accept both user auth and internal service auth (for Streamlit chat app)
    from ichrisbirch.api.endpoints.auth import require_user_or_internal_service

    chat_deps = [Depends(require_user_or_internal_service)]
    api.include_router(endpoints.chat.chats.router, prefix='/chat/chats', dependencies=chat_deps)
    api.include_router(endpoints.chat.messages.router, prefix='/chat/messages', dependencies=chat_deps)
    api.include_router(endpoints.events.router, prefix='/events', dependencies=deps)
    api.include_router(endpoints.habits.router, prefix='/habits', dependencies=deps)
    api.include_router(endpoints.money_wasted.router, prefix='/money-wasted', dependencies=deps)
    api.include_router(endpoints.server.router, prefix='/server', dependencies=deps)
    api.include_router(endpoints.tasks.router, prefix='/tasks', dependencies=deps)
    api.include_router(endpoints.users.router, prefix='/users')
    logger.info('routers_registered')

    api.add_exception_handler(HTTPException, http_exception_handler_logger)
    api.add_exception_handler(RequestValidationError, request_validation_exception_handler_logger)
    api.add_exception_handler(Exception, api_exception_handler)
    logger.info('exception_handlers_registered')

    logger.info('api_initialized')
    return api
