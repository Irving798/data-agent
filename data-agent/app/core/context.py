"""保存当前请求标识，使异步调用链能够统一关联日志。"""

from contextvars import ContextVar

request_id_ctx_var = ContextVar("request_id", default="1")

