import logging

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
from ichrisbirch.config import get_settings
from ichrisbirch.util import log_caller

logger = logging.getLogger('api.main')


async def http_exception_handler_logger(request, exc):
    logger.error(f'api error: {request.url.path} - {exc}')
    return await http_exception_handler(request, exc)


async def request_validation_exception_handler_logger(request, exc):
    logger.error(f'api validation error: {request.url.path} - {exc}')
    return await request_validation_exception_handler(request, exc)


async def api_exception_handler(request, exc):
    logger.error(f'api unhandled error: {request.url.path} - {exc}')
    return JSONResponse(status_code=500, content={'message': f'Internal server error: {type(exc).__name__}'})


@log_caller
def create_api(settings: Settings = Depends(get_settings)) -> FastAPI:
    api = FastAPI(title=settings.fastapi.title, description=settings.fastapi.description)
    logger.info('initializing api')

    # get the settings but then override the function with constant settings to avoid
    # accidentally reloading with different values throughout the app
    api.dependency_overrides[get_settings] = lambda: settings
    logger.info(f'loaded settings: {type(settings)}')
    logger.debug(f'api url: {settings.api_url}')
    logger.debug(f'postgres port: {settings.postgres.port}')
    logger.debug(f'postgres uri: {settings.postgres.db_uri}')
    logger.debug(f'sqlalchemy port: {settings.sqlalchemy.port}')
    logger.debug(f'sqlalchemy uri: {settings.sqlalchemy.db_uri}')

    api.add_middleware(ResponseLoggerMiddleware)
    logger.info('response logger middleware added')

    api.add_middleware(
        CORSMiddleware,
        allow_origins=settings.fastapi.allowed_origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    logger.info('cors middleware added')

    deps = [Depends(get_current_user)]

    api.include_router(endpoints.home.router, prefix='', include_in_schema=False)
    api.include_router(endpoints.admin.router, prefix='/admin', dependencies=[Depends(get_admin_user)])
    api.include_router(endpoints.articles.router, prefix='/articles', dependencies=deps)
    api.include_router(endpoints.auth.router, prefix='/auth')
    api.include_router(endpoints.autotasks.router, prefix='/autotasks', dependencies=deps)
    api.include_router(endpoints.books.router, prefix='/books', dependencies=deps)
    api.include_router(endpoints.box_packing.router, prefix='/box-packing', dependencies=deps)
    api.include_router(endpoints.countdowns.router, prefix='/countdowns', dependencies=deps)
    api.include_router(endpoints.chat.chats.router, prefix='/chat/chats', dependencies=deps)
    api.include_router(endpoints.chat.messages.router, prefix='/chat/messages', dependencies=deps)
    api.include_router(endpoints.events.router, prefix='/events', dependencies=deps)
    api.include_router(endpoints.habits.router, prefix='/habits', dependencies=deps)
    api.include_router(endpoints.money_wasted.router, prefix='/money-wasted', dependencies=deps)
    api.include_router(endpoints.server.router, prefix='/server', dependencies=deps)
    api.include_router(endpoints.tasks.router, prefix='/tasks', dependencies=deps)
    api.include_router(endpoints.users.router, prefix='/users', dependencies=deps)
    logger.info('routers registered')

    api.add_exception_handler(HTTPException, http_exception_handler_logger)
    api.add_exception_handler(RequestValidationError, request_validation_exception_handler_logger)
    api.add_exception_handler(Exception, api_exception_handler)
    logger.info('exception handlers registered')

    logger.info('initialized api successfully')
    return api
