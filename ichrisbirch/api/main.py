import logging

from fastapi import FastAPI

from ichrisbirch.api import endpoints

# from ichrisbirch.api.middleware import ResponseLoggerMiddleware
from ichrisbirch.config import Settings

# TODO: for authentication
# from ichrisbirch.api.dependencies import get_query_token, get_token_header
logger = logging.getLogger(__name__)


def create_api(settings: Settings) -> FastAPI:
    api = FastAPI(title=settings.fastapi.title, description=settings.fastapi.description)
    logger.info('FastAPI Started')

    # api.add_middleware(ResponseLoggerMiddleware)
    # logger.debug(f'Added middleware to FastAPI: {ResponseLoggerMiddleware.__name__}')

    # TODO: for auth
    # app = FastAPI(dependencies=[Depends(get_query_token)])

    # Add dependencies later
    # dependencies=[Depends(auth)],

    api.include_router(endpoints.home.router)
    api.include_router(endpoints.autotasks.router)
    api.include_router(endpoints.countdowns.router)
    api.include_router(endpoints.events.router)
    api.include_router(endpoints.health.router)
    api.include_router(endpoints.tasks.router)

    logger.info('FastAPI Routers Registered')
    return api
