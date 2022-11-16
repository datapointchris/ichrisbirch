import logging
import random
import string
import time

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

# from .dependencies import get_query_token, get_token_header
from .endpoints import tasks, health
from euphoria import __version__
from euphoria.backend.common import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
# fh = logging.FileHandler(filename='fastapi.log')
formatter = logging.Formatter(
    "%(asctime)s | %(name)s:%(lineno)d | %(levelname)s: %(message)s"
)
ch.setFormatter(formatter)
# fh.setFormatter(formatter)
logger.addHandler(ch)  # Exporting logs to the screen
# logger.addHandler(fh)  # Exporting logs to a file

# app = FastAPI(dependencies=[Depends(get_query_token)])

api_description = """
### All API are awesome

- Do markdown here
"""

api = FastAPI(title='Euphoria API', description=api_description, version=__version__)


@api.middleware("http")
async def log_requests(request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"rid={idem} start request path={request.url.path}")
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(
        f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}"
    )
    return response


# responses for all apis
responses = {
    404: {'description': 'Not found'},
    403: {"description": "Operation forbidden"},
}

# Add dependencies later
# dependencies=[Depends(auth)],

api.include_router(tasks.router, responses=responses)
api.include_router(health.router, responses=responses)
# api.include_router(items.router)
print('RUNNING FASTAPI')
print(f'config.ENVIRONMENT: {config.ENVIRONMENT}')
print(f'config.API_URL: {config.API_URL}')
print(f'config.SQLALCHEMY_DATABASE_URI: {config.sqlalchemy.SQLALCHEMY_DATABASE_URI}')
logger.info('RUNNING FASTAPI')
logger.info(f'config.ENVIRONMENT: {config.ENVIRONMENT}')
logger.info(f'config.API_URL: {config.API_URL}')
logger.info(f'config.POSTGRES_DATABASE_URI: {config.postgres.POSTGRES_DATABASE_URI}')


@api.get("/", include_in_schema=False)
async def docs_redirect():
    # return RedirectResponse(url='/docs')
    return {'message': 'This is the home page, no redirction'}
