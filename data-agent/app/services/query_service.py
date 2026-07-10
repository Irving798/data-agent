import json

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agent.context import DataAgentContext
from app.agent.graph import graph
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.prompt.prompt_loader import load_prompt
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.intent_classifier import QueryIntent, classify_query_intent


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
        prompt_name = (
            "clarify_query" if intent == QueryIntent.UNCLEAR else "chat_reply"
        )
        prompt = PromptTemplate(
            template=load_prompt(prompt_name),
            input_variables=["query"],
        )
        chain = prompt | llm | StrOutputParser()
        return await chain.ainvoke({"query": query})

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
