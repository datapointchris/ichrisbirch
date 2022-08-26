from fastapi import Depends, FastAPI

from .dependencies import get_query_token, get_token_header
from .endpoints import tasks
from ..common.config import env_config
from ..common.db.sqlalchemy.base_class import Base
from ..common.db.sqlalchemy.session import engine
import logging
import random
import string
import time

# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
# ch = logging.StreamHandler()
# fh = logging.FileHandler(filename='fastapi.log')
# formatter = logging.Formatter(
#     "%(asctime)s - %(name)s - %(levelname)s: %(message)s <= `%(funcName)s` %(module)s:%(lineno)d %(pathname)s"
# )
# ch.setFormatter(formatter)
# fh.setFormatter(formatter)
# logger.addHandler(ch)  # Exporting logs to the screen
# logger.addHandler(fh)  # Exporting logs to a file


# app = FastAPI(dependencies=[Depends(get_query_token)])

# 1. Create app
app = FastAPI()

# 2. Add config to ride around
# Do I need to do this
app.config = env_config

# 3. Create tables
Base.metadata.create_all(bind=engine)



# @app.middleware("http")
# async def log_requests(request, call_next):
#     idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
#     logger.info(f"rid={idem} start request path={request.url.path}")
#     start_time = time.time()

#     response = await call_next(request)

#     process_time = (time.time() - start_time) * 1000
#     formatted_process_time = '{0:.2f}'.format(process_time)
#     logger.info(
#         f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}"
#     )

#     return response


# responses for all apps
responses = {
    404: {'description': 'Not found'},
    403: {"description": "Operation forbidden"},
}

# Add dependencies later
# dependencies=[Depends(auth)],

app.include_router(tasks.router, responses=responses)
# app.include_router(items.router)
# logger.info('RUNNING FASTAPI')


@app.get("/")
async def root():
    print('BROKEN')
    return {"message": "This is the API"}
