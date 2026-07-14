"""定义字段与业务指标关联关系的领域实体。"""

from dataclasses import dataclass


@dataclass
class ColumnMetric:
    column_id: str
    metric_id: str
