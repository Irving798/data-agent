from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from app.conf.app_config import QueryExecutionConfig
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository


class AsyncRows:
    def __init__(self, rows):
        self.rows = rows

    def mappings(self):
        return self

    def __aiter__(self):
        return self._iterate()

    async def _iterate(self):
        for row in self.rows:
            yield row


class DWMySQLRepositoryTest(IsolatedAsyncioTestCase):
    def create_repository(
        self,
        rows,
        *,
        max_rows=2,
        timeout_ms=1000,
        max_result_bytes=1024,
    ):
        session = AsyncMock()
        session.stream.return_value = AsyncRows(rows)
        config = QueryExecutionConfig(
            max_rows=max_rows,
            timeout_ms=timeout_ms,
            max_result_bytes=max_result_bytes,
        )
        return DWMySQLRepository(session, config), session

    async def test_limits_rows_and_reports_truncation(self):
        repository, session = self.create_repository(
            [{"id": 1}, {"id": 2}, {"id": 3}]
        )

        result = await repository.execute_sql("SELECT id FROM fact_order")

        self.assertEqual(result.rows, [{"id": 1}, {"id": 2}])
        self.assertTrue(result.truncated)
        self.assertEqual(result.truncation_reason, "max_rows")
        executed_sql = str(session.stream.await_args.args[0])
        self.assertIn("LIMIT 3", executed_sql)

    async def test_limits_serialized_result_size(self):
        repository, _ = self.create_repository(
            [{"name": "first"}, {"name": "second"}],
            max_rows=10,
            max_result_bytes=18,
        )

        result = await repository.execute_sql("SELECT name FROM dim_product")

        self.assertEqual(result.rows, [{"name": "first"}])
        self.assertTrue(result.truncated)
        self.assertEqual(result.truncation_reason, "max_result_bytes")

    async def test_sets_mysql_timeout(self):
        repository, session = self.create_repository([])

        await repository.execute_sql("SELECT 1")

        timeout_sql = str(session.execute.await_args.args[0])
        self.assertEqual(timeout_sql, "SET SESSION MAX_EXECUTION_TIME = 1000")

    async def test_rejects_multiple_or_non_query_statements(self):
        repository, session = self.create_repository([])

        with self.assertRaisesRegex(ValueError, "Only one query statement"):
            await repository.execute_sql("SELECT 1; SELECT 2")
        with self.assertRaisesRegex(ValueError, "Only one query statement"):
            await repository.execute_sql("DELETE FROM fact_order")

        session.stream.assert_not_awaited()

    async def test_preserves_a_smaller_existing_limit(self):
        repository, session = self.create_repository([], max_rows=100)

        await repository.execute_sql("SELECT id FROM fact_order LIMIT 10")

        executed_sql = str(session.stream.await_args.args[0])
        self.assertIn("LIMIT 10", executed_sql)
