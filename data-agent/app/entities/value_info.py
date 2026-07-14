"""定义可供全文检索召回的字段真实取值。"""

from dataclasses import dataclass


@dataclass
class ValueInfo:
    id: str
    value: str
    column_id: str
