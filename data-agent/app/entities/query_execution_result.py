from dataclasses import dataclass


@dataclass(frozen=True)
class QueryExecutionResult:
    rows: list[dict]
    truncated: bool
    truncation_reason: str | None
    max_rows: int
    max_result_bytes: int
