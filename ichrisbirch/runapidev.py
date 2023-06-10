import uvicorn

from ichrisbirch.logger import create_base_logger

if __name__ == "__main__":
    logger = create_base_logger()
    uvicorn.run('ichrisbirch.wsgi:api', port=6200, reload=True, log_level="debug")
