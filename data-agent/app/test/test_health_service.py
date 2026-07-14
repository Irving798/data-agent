"""验证依赖服务健康状态的并发汇总逻辑。"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from app.services.health_service import HealthService


class HealthServiceTest(IsolatedAsyncioTestCase):
    def setUp(self):
        self.meta_mysql_session = AsyncMock()
        self.dw_mysql_session = AsyncMock()
        self.es_client = AsyncMock()
        self.qdrant_client = AsyncMock()
        self.es_client.ping.return_value = True

    def create_service(self):
        return HealthService(
            meta_mysql_session=self.meta_mysql_session,
            dw_mysql_session=self.dw_mysql_session,
            es_client=self.es_client,
            qdrant_client=self.qdrant_client,
        )

    async def test_returns_healthy_when_all_services_are_available(self):
        result = await self.create_service().check()

        self.assertEqual(result["status"], "healthy")
        self.assertTrue(
            all(
                service["status"] == "healthy"
                for service in result["services"].values()
            )
        )

    async def test_returns_degraded_when_one_service_is_unavailable(self):
        self.es_client.ping.side_effect = ConnectionError("unavailable")

        result = await self.create_service().check()

        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["services"]["elasticsearch"]["status"], "unhealthy")
        self.assertEqual(result["services"]["mysql"]["status"], "healthy")
        self.assertEqual(result["services"]["qdrant"]["status"], "healthy")
