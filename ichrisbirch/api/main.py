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

    api.include_router(
        endpoints.home.router,
        prefix='',
        tags=['home'],
        include_in_schema=False,
        responses=settings.fastapi.responses,
    )
    api.include_router(
        endpoints.autotasks.router,
        prefix='/autotasks',
        tags=['autotasks'],
        responses=settings.fastapi.responses,
    )
    api.include_router(
        endpoints.countdowns.router,
        prefix='/countdowns',
        tags=['countdowns'],
        responses=settings.fastapi.responses,
    )
    api.include_router(
        endpoints.health.router,
        prefix='/health',
        tags=['health'],
        responses=settings.fastapi.responses,
    )
    api.include_router(
        endpoints.tasks.router,
        prefix='/tasks',
        tags=['tasks'],
        responses=settings.fastapi.responses,
    )

    logger.debug('Registered API Routers')
    return api
