"""管理 Embedding 客户端的创建、访问和资源释放。"""

# from typing import Optional
#
# from langchain_huggingface import HuggingFaceEndpointEmbeddings
#
# from app.conf.app_config import EmbeddingConfig, app_config
#
#
# class EmbeddingClientManager:
#     def __init__(self, config: EmbeddingConfig):
#         self.client: Optional[HuggingFaceEndpointEmbeddings] = None
#         self.config = config
#
#     def _get_url(self):
#         return f"http://{self.config.host}:{self.config.port}"
#
#     def init(self):
#         self.client = HuggingFaceEndpointEmbeddings(model=self._get_url())
#
#
# embedding_client_manager = EmbeddingClientManager(app_config.embedding)

from typing import Optional

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_openai import OpenAIEmbeddings

from app.conf.app_config import EmbeddingConfig, app_config


class EmbeddingClientManager:
    def __init__(self, config: EmbeddingConfig):
        self.client: Optional[Embeddings] = None
        self.config = config

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        if self.config.provider == "tei":
            self.client = HuggingFaceEndpointEmbeddings(model=self._get_url())
            return

        if self.config.provider == "openai_compatible":
            self.client = OpenAIEmbeddings(
                model=self.config.model,
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                dimensions=self.config.dimensions,
                check_embedding_ctx_length=False,
            )

            return

        raise ValueError(f"Unsupported embedding provider: {self.config.provider}")


embedding_client_manager = EmbeddingClientManager(app_config.embedding)

