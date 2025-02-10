import logging

from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ichrisbirch.api import endpoints
from ichrisbirch.api.middleware import ResponseLoggerMiddleware
from ichrisbirch.config import Settings

# TODO: for authentication
# from ichrisbirch.api.dependencies import get_query_token, get_token_header
logger = logging.getLogger('api.main')


async def http_exception_handler_logger(request, exc):
    logger.error(f'api error: {exc}')
    return await http_exception_handler(request, exc)


async def request_validation_exception_handler_logger(request, exc):
    logger.error(f'api error: {exc}')
    return await request_validation_exception_handler(request, exc)


async def generic_exception_handler(request, exc):
    logger.error(f'api error: {exc}')
    return JSONResponse(status_code=500, content={'message': f'api error: {exc}'})


def create_api(settings: Settings) -> FastAPI:
    api = FastAPI(title=settings.fastapi.title, description=settings.fastapi.description)
    logger.info('initializing')

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

    # TODO: for auth
    # app = FastAPI(dependencies=[Depends(get_query_token)])

    # Add dependencies later
    # dependencies=[Depends(auth)],

    api.include_router(endpoints.home.router, prefix='', tags=['home'], include_in_schema=False)
    api.include_router(endpoints.admin.router, prefix='/admin', tags=['admin'])
    api.include_router(endpoints.articles.router, prefix='/articles', tags=['articles'])
    api.include_router(endpoints.auth.router, prefix='/auth', tags=['auth'])
    api.include_router(endpoints.autotasks.router, prefix='/autotasks', tags=['autotasks'])
    api.include_router(endpoints.books.router, prefix='/books', tags=['books'])
    api.include_router(endpoints.box_packing.router, prefix='/box-packing', tags=['box packing'])
    api.include_router(endpoints.countdowns.router, prefix='/countdowns', tags=['countdowns'])
    api.include_router(endpoints.chat.chats.router, prefix='/chat/chats', tags=['chats'])
    api.include_router(endpoints.chat.messages.router, prefix='/chat/messages', tags=['messages'])
    api.include_router(endpoints.events.router, prefix='/events', tags=['events'])
    api.include_router(endpoints.habits.router, prefix='/habits', tags=['habits'])
    api.include_router(endpoints.money_wasted.router, prefix='/money-wasted', tags=['money', 'money wasted'])
    api.include_router(endpoints.server.router, prefix='/server', tags=['server'])
    api.include_router(endpoints.tasks.router, prefix='/tasks', tags=['tasks'])
    api.include_router(endpoints.users.router, prefix='/users', tags=['users'])
    logger.info('routers registered')

    api.add_exception_handler(HTTPException, http_exception_handler_logger)
    api.add_exception_handler(RequestValidationError, request_validation_exception_handler_logger)
    api.add_exception_handler(Exception, generic_exception_handler)
    logger.info('exception handlers registered')

    logger.info('initialized successfully')
    return api
