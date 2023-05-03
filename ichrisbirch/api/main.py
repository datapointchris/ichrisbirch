import logging

from fastapi import FastAPI

from ichrisbirch.api import endpoints
from ichrisbirch.api.middleware import ResponseLoggerMiddleware

# TODO: for authentication
# from ichrisbirch.api.dependencies import get_query_token, get_token_header

logger = logging.getLogger(__name__)


def create_api(settings) -> FastAPI:
    """FastAPI app factory

    Returns:
        FastAPI: FastAPI app
    """
    api = FastAPI(title=settings.fastapi.title, description=settings.fastapi.description, version=settings.version)
    logger.debug(f'{api.title} {api.version} Started')

    api.add_middleware(ResponseLoggerMiddleware)
    logger.debug(f'Added middleware to FastAPI: {ResponseLoggerMiddleware.__name__}')

    # TODO: for auth
    # app = FastAPI(dependencies=[Depends(get_query_token)])

    # Add dependencies later
    # dependencies=[Depends(auth)],

    api.include_router(endpoints.main.router, responses=settings.fastapi.responses)
    api.include_router(endpoints.autotasks.router, responses=settings.fastapi.responses)
    api.include_router(endpoints.health.router, responses=settings.fastapi.responses)
    api.include_router(endpoints.tasks.router, responses=settings.fastapi.responses)

    logger.debug('Registered API Routers')
    return api
