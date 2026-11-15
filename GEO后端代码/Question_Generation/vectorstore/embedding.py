"""
本地Embedding模型封装

加载本地训练好的embedding模型
"""

from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential
from config.settings import settings


class EmbeddingModel:
    """本地Embedding模型"""

    def __init__(self):
        self.model_path = settings.embedding.model_path
        self._model = None

    def _load_model(self):
        """延迟加载模型"""
        if self._model is None:
            print(f"[DEBUG] Loading Embedding model from {self.model_path}...")
            from sentence_transformers import SentenceTransformer
            print(f"[DEBUG] Initializing SentenceTransformer...")
            self._model = SentenceTransformer(self.model_path)
            print(f"[DEBUG] Embedding model loaded!")
        return self._model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量文本embedding"""
        model = self._load_model()
        embeddings = model.encode(texts)
        return [emb.tolist() for emb in embeddings]