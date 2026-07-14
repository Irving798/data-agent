"""提供数据服务健康状态查询接口。"""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_health_service
from app.api.schemas.health_schema import HealthResponseSchema
from app.services.health_service import HealthService

health_router = APIRouter(prefix="/api", tags=["health"])


@health_router.get("/health", response_model=HealthResponseSchema)
async def health(
    health_service: HealthService = Depends(get_health_service),
):
    return await health_service.check()
