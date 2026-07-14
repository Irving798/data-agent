"""定义自然语言查询接口的请求参数。"""

from pydantic import BaseModel


class QuerySchema(BaseModel):
    query: str
