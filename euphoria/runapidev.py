import uvicorn
import os

os.environ['ENVIRONMENT'] = 'development'
os.environ['FASTAPI_ENV'] = 'development'

if __name__ == "__main__":
    uvicorn.run("backend.api.main:app", reload=True, port=8000, log_level="debug")
