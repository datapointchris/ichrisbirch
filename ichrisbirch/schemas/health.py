from pydantic import BaseModel


class Health(BaseModel):
    """Pydantic Model for Health endpoint"""

    name: str
    version: str
    environment: str
    api_url: str
    log_level: str
    server_time: str
    local_time: str
