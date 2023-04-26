import uvicorn

from ichrisbirch import base_logger
from ichrisbirch.config import settings

if __name__ == "__main__":
    base_logger.init(settings)
    uvicorn.run('ichrisbirch.wsgi:api', port=6200, reload=True, log_level="debug")
