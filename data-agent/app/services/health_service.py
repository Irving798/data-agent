import asyncio
from datetime import datetime, timezone
from time import perf_counter
from typing import Awaitable, Callable

from elasticsearch import AsyncElasticsearch
from qdrant_client import AsyncQdrantClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import logger


class HealthService:
    """检查应用依赖的数据服务，并返回统一的健康状态。"""

    def __init__(
        self,
        meta_mysql_session: AsyncSession,
        dw_mysql_session: AsyncSession,
        es_client: AsyncElasticsearch,
        qdrant_client: AsyncQdrantClient,
        timeout_seconds: float = 2.0,
    ):
        self.meta_mysql_session = meta_mysql_session
        self.dw_mysql_session = dw_mysql_session
        self.es_client = es_client
        self.qdrant_client = qdrant_client
        self.timeout_seconds = timeout_seconds

    async def _check_mysql(self):
        await asyncio.gather(
            self.meta_mysql_session.execute(text("SELECT 1")),
            self.dw_mysql_session.execute(text("SELECT 1")),
        )

    async def _check_elasticsearch(self):
        if not await self.es_client.ping():
            raise ConnectionError("Elasticsearch ping failed")

    async def _check_qdrant(self):
        await self.qdrant_client.get_collections()

    async def _run_check(
        self,
        service_name: str,
        check: Callable[[], Awaitable[None]],
    ) -> dict:
        started_at = perf_counter()
        try:
            async with asyncio.timeout(self.timeout_seconds):
                await check()
            return {
                "status": "healthy",
                "latency_ms": round((perf_counter() - started_at) * 1000),
                "message": None,
            }
        except Exception as error:
            logger.warning(f"{service_name} 健康检查失败: {error}")
            return {
                "status": "unhealthy",
                "latency_ms": round((perf_counter() - started_at) * 1000),
                "message": "服务不可用",
            }

    async def check(self) -> dict:
        mysql, elasticsearch, qdrant = await asyncio.gather(
            self._run_check("MySQL", self._check_mysql),
            self._run_check("Elasticsearch", self._check_elasticsearch),
            self._run_check("Qdrant", self._check_qdrant),
        )
        services = {
            "mysql": mysql,
            "elasticsearch": elasticsearch,
            "qdrant": qdrant,
        }
        overall_status = (
            "healthy"
            if all(service["status"] == "healthy" for service in services.values())
            else "degraded"
        )
        return {
            "status": overall_status,
            "services": services,
            "checked_at": datetime.now(timezone.utc),
        }
