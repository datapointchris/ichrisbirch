import logging

from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ichrisbirch.api import endpoints
from ichrisbirch.api.middleware import ResponseLoggerMiddleware
from ichrisbirch.config import Settings

# TODO: for authentication
# from ichrisbirch.api.dependencies import get_query_token, get_token_header
logger = logging.getLogger(__name__)


async def http_exception_handler_logger(request, exc):
    logger.error(repr(exc))
    return await http_exception_handler(request, exc)


async def request_validation_exception_handler_logger(request, exc):
    logger.error(repr(exc))
    return await request_validation_exception_handler(request, exc)


async def generic_exception_handler(request, exc):
    logger.error(repr(exc))
    return JSONResponse(status_code=500, content={"message": repr(exc)})


def create_api(settings: Settings) -> FastAPI:
    api = FastAPI(title=settings.fastapi.title, description=settings.fastapi.description)
    logger.info('FastAPI Started')

    api.add_middleware(ResponseLoggerMiddleware)
    logger.debug(f'FastAPI middleware added: {ResponseLoggerMiddleware.__name__}')

    # TODO: for auth
    # app = FastAPI(dependencies=[Depends(get_query_token)])

    # Add dependencies later
    # dependencies=[Depends(auth)],

    api.include_router(endpoints.home.router, prefix='', tags=['home'], include_in_schema=False)
    api.include_router(endpoints.autotasks.router, prefix='/autotasks', tags=['autotasks'])
    api.include_router(endpoints.box_packing.router, prefix='/box_packing', tags=['box_packing'])
    api.include_router(endpoints.countdowns.router, prefix='/countdowns', tags=['countdowns'])
    api.include_router(endpoints.events.router, prefix='/events', tags=['events'])
    api.include_router(endpoints.habits.router, prefix='/habits', tags=['habits'])
    api.include_router(endpoints.server.router, prefix='/server', tags=['server'])
    api.include_router(endpoints.tasks.router, prefix='/tasks', tags=['tasks'])
    api.include_router(endpoints.users.router, prefix='/users', tags=['users'])
    logger.info('FastAPI Routers Registered')

    api.add_exception_handler(HTTPException, http_exception_handler_logger)
    api.add_exception_handler(RequestValidationError, request_validation_exception_handler_logger)
    api.add_exception_handler(Exception, generic_exception_handler)
    logger.info('FastAPI Exception Handlers Registered')

    return api
