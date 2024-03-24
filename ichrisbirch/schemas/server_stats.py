from pydantic import BaseModel


class ServerStats(BaseModel):
    name: str
    environment: str
    api_url: str
    log_level: str
    server_time: str
    local_time: str
