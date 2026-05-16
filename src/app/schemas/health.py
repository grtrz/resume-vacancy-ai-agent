from pydantic import BaseModel


class HealthCheck(BaseModel):
    status: str
    service: str
    environment: str


class RootInfo(BaseModel):
    service: str
    environment: str
    description: str
    docs_url: str
    health_url: str
