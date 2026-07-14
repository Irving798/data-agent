"""封装 SQL 查询结果以及截断、耗时等执行元信息。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class QueryExecutionResult:
    rows: list[dict]
    truncated: bool
    truncation_reason: str | None
    max_rows: int
    max_result_bytes: int
