from pydantic import BaseModel


class Health(BaseModel):
    name: str
    version: str
    server_time: str