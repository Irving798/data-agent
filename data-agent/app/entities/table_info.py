"""定义数据仓库表及其字段集合的领域实体。"""

from dataclasses import dataclass


@dataclass
class TableInfo:
    id: str
    name: str
    role: str
    description: str
