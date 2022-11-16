from pydantic import BaseModel


class Health(BaseModel):
    name: str
    version: str
    environment: str
    configENVIRONMENT: str
    api_url: str
    configAPI_URL: str
    server_time: str
