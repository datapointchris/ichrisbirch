import logging
import random
import string
import time

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from ichrisbirch import __version__

# from .dependencies import get_query_token, get_token_header
from .endpoints import health, tasks

logger = logging.getLogger(__name__)
# app = FastAPI(dependencies=[Depends(get_query_token)])

api_description = """
### All API are awesome

- Do markdown here
"""

api = FastAPI(title='Euphoria API', description=api_description, version=__version__)
logger.debug(f'{api.title} {api.version} Started')


@api.middleware("http")
async def log_requests(request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.debug(f"rid={idem} start request path={request.url.path}")
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.debug(
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


@api.get("/", include_in_schema=False)
async def docs_redirect():
    # return RedirectResponse(url='/docs')
    return {'message': 'This is the home page, no redirction'}
