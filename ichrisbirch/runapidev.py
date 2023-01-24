import uvicorn


if __name__ == "__main__":
    uvicorn.run("euphoria.wsgi:api", port=6200, reload=True, log_level="debug")
