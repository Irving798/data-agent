from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.query_execution_result import QueryExecutionResult


async def execute_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "执行SQL", "status": "running"})

    sql = state["sql"]

    dw_mysql_repository = runtime.context["dw_mysql_repository"]

    try:
        result: QueryExecutionResult = await dw_mysql_repository.execute_sql(sql)

        writer({"type": "progress", "step": "执行SQL", "status": "success"})
        writer(
            {
                "type": "result",
                "data": result.rows,
                "truncated": result.truncated,
                "truncation_reason": result.truncation_reason,
                "limits": {
                    "max_rows": result.max_rows,
                    "max_result_bytes": result.max_result_bytes,
                },
            }
        )
        logger.info(
            f"执行SQL完成: rows={len(result.rows)}, truncated={result.truncated}, "
            f"truncation_reason={result.truncation_reason}"
        )


    except Exception as e:
        writer({"type": "progress", "step": "执行SQL", "status": "error"})
        logger.error(f"执行SQL失败:{str(e)}")
        raise
