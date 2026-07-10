import json

from sqlglot import exp, parse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.conf.app_config import QueryExecutionConfig, app_config
from app.entities.query_execution_result import QueryExecutionResult


class DWMySQLRepository:
    def __init__(
        self,
        session: AsyncSession,
        query_config: QueryExecutionConfig | None = None,
    ):
        self.session = session
        self.query_config = query_config or app_config.query_execution
        if (
            self.query_config.max_rows <= 0
            or self.query_config.timeout_ms <= 0
            or self.query_config.max_result_bytes <= 0
        ):
            raise ValueError("Query execution limits must be positive integers")

    def _build_bounded_query(self, sql: str) -> str:
        statements = parse(sql, read="mysql")
        if len(statements) != 1 or not isinstance(statements[0], exp.Query):
            raise ValueError("Only one query statement is allowed")

        query = statements[0]
        existing_limit = query.args.get("limit")
        fetch_limit = self.query_config.max_rows + 1
        if existing_limit and isinstance(existing_limit.expression, exp.Literal):
            try:
                fetch_limit = min(fetch_limit, int(existing_limit.expression.this))
            except (TypeError, ValueError):
                pass

        return query.limit(fetch_limit, copy=True).sql(dialect="mysql")

    async def get_column_types(self, table_name: str) -> dict[str, str]:
        sql = f"show columns from {table_name}"
        result = await self.session.execute(text(sql))
        return {row.Field: row.Type for row in result.fetchall()}

    async def get_column_values(self, table_name: str, column_name: str, limit: int):
        sql = f"select distinct {column_name} from {table_name} limit {limit}"
        result = await self.session.execute(text(sql))
        return result.scalars().fetchall()

    async def get_db_info(self):
        result = await self.session.execute(text("select version()"))
        version = result.scalar()

        dialect = self.session.get_bind().dialect.name

        return {'version': version, 'dialect': dialect}

    async def validate_sql(self, sql):
        bounded_sql = self._build_bounded_query(sql)
        await self.session.execute(text(f"explain {bounded_sql}"))

    async def execute_sql(self, sql: str) -> QueryExecutionResult:
        bounded_sql = self._build_bounded_query(sql)
        await self.session.execute(
            text(
                "SET SESSION MAX_EXECUTION_TIME = "
                f"{self.query_config.timeout_ms}"
            )
        )

        result = await self.session.stream(text(bounded_sql))
        rows: list[dict] = []
        result_bytes = 0
        truncated = False
        truncation_reason = None

        async for row in result.mappings():
            if len(rows) >= self.query_config.max_rows:
                truncated = True
                truncation_reason = "max_rows"
                break

            current_row = dict(row)
            current_row_bytes = len(
                json.dumps(
                    current_row,
                    ensure_ascii=False,
                    default=str,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            if result_bytes + current_row_bytes > self.query_config.max_result_bytes:
                truncated = True
                truncation_reason = "max_result_bytes"
                break

            rows.append(current_row)
            result_bytes += current_row_bytes

        return QueryExecutionResult(
            rows=rows,
            truncated=truncated,
            truncation_reason=truncation_reason,
            max_rows=self.query_config.max_rows,
            max_result_bytes=self.query_config.max_result_bytes,
        )
