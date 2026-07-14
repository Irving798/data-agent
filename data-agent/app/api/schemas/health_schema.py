"""定义健康检查接口的结构化响应。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ServiceHealthSchema(BaseModel):
    status: Literal["healthy", "unhealthy"]
    latency_ms: int
    message: str | None = None


class HealthServicesSchema(BaseModel):
    mysql: ServiceHealthSchema
    elasticsearch: ServiceHealthSchema
    qdrant: ServiceHealthSchema


class HealthResponseSchema(BaseModel):
    status: Literal["healthy", "degraded"]
    services: HealthServicesSchema
    checked_at: datetime
