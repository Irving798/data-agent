import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agent.context import DataAgentContext
from app.agent.graph import graph
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.intent_classifier import QueryIntent, classify_query_intent

CHAT_SYSTEM_PROMPT = """
你是 Data Agent 的智能问数助手。
用户当前输入被判断为闲聊、问候、感谢或使用说明类问题。
请自然、简洁地回复，语气友好。
你可以介绍自己能帮助用户查询订单分析 Demo 数据，例如销售额、销量、订单、地区、商品品类、会员等级等。
不要编造任何具体业务数据、SQL、数据库查询结果或系统已经执行过的分析。
如果用户想查具体数据，请引导他提出明确的数据问题。
""".strip()

CLARIFY_SYSTEM_PROMPT = """
你是 Data Agent 的智能问数助手。
用户的问题可能和业务分析有关，但缺少明确指标、维度或时间范围。
请不要编造数据，也不要假装已经查询数据库。
请用一句简洁的话追问用户，让用户补充他想查询的指标或维度。
可以给 2 到 3 个示例方向，例如销售额、销量、订单量、地区、商品品类、会员等级。
""".strip()


class QueryService:
    """查询服务：负责组装 DataAgent 运行所需依赖，并以流式方式返回查询结果。"""

    def __init__(
        self,
        embedding_client: HuggingFaceEndpointEmbeddings,
        column_qdrant_repository: ColumnQdrantRepository,
        value_es_repository: ValueESRepository,
        metric_qdrant_repository: MetricQdrantRepository,
        meta_mysql_repository: MetaMySQLRepository,
        dw_mysql_repository: DWMySQLRepository,
    ):
        self.embedding_client = embedding_client
        self.column_qdrant_repository = column_qdrant_repository
        self.value_es_repository = value_es_repository
        self.metric_qdrant_repository = metric_qdrant_repository
        self.meta_mysql_repository = meta_mysql_repository
        self.dw_mysql_repository = dw_mysql_repository

    async def _reply_with_llm(self, query: str, intent: QueryIntent) -> str:
        system_prompt = (
            CLARIFY_SYSTEM_PROMPT if intent == QueryIntent.UNCLEAR else CHAT_SYSTEM_PROMPT
        )
        response = await llm.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=query)]
        )
        content = getattr(response, "content", response)
        if isinstance(content, list):
            return "".join(str(item) for item in content)
        return str(content)

    async def query(self, query: str):
        intent = classify_query_intent(query)
        if intent != QueryIntent.DATA_QUERY:
            try:
                content = await self._reply_with_llm(query, intent)
                payload = {"type": "text", "content": content}
            except Exception as e:
                payload = {"type": "error", "message": f"闲聊回复生成失败：{e}"}
            yield f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"
            return

        context = DataAgentContext(
            embedding_client=self.embedding_client,
            column_qdrant_repository=self.column_qdrant_repository,
            value_es_repository=self.value_es_repository,
            metric_qdrant_repository=self.metric_qdrant_repository,
            meta_mysql_repository=self.meta_mysql_repository,
            dw_mysql_repository=self.dw_mysql_repository,
        )
        state = DataAgentState(query=query)
        try:
            async for chunk in graph.astream(
                input=state, context=context, stream_mode="custom"
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False, default=str)}\n\n"
        except Exception as e:
            payload = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"
