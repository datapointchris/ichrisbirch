import uvicorn
import os

os.environ['ENVIRONMENT'] = 'development'
os.environ['FASTAPI_ENV'] = 'development'

if __name__ == "__main__":
    uvicorn.run("backend.api.main:app", host='0.0.0.0', port=6200, reload=True, log_level="debug")
