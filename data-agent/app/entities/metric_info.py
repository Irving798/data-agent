"""定义业务指标及其关联字段的领域实体。"""

from dataclasses import dataclass


@dataclass
class MetricInfo:
    id: str
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]
