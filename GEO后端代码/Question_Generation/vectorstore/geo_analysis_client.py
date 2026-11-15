"""
GEO Analysis Milvus Client

处理GEO分析详细结果的存储和查询
"""

import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from pymilvus import connections, Collection, utility

from .geo_analysis_schema import get_geo_schema, GEOAnalysisSchema
from .embedding import EmbeddingModel


class GEOAnalysisClient:
    """
    GEO Analysis Collection 客户端

    存储和查询GEO分析详细结果
    """

    def __init__(
        self,
        collection_name: str,
        host: str = "./milvus_data/milvus.db",
    ):
        self.host = host
        self.collection_name = collection_name
        self._collection: Optional[Collection] = None
        self._connected = False
        self.embedding_model = EmbeddingModel()

    def connect(self):
        """连接到Milvus服务器"""
        if not self._connected:
            # keepalive设置（避免too_many_pings警告）
            keepalive_settings = {
                "keepalive_interval_ms": 60000,  # 心跳间隔60秒
                "keepalive_timeout_ms": 20000,   # 心跳超时20秒
            }

            # 检查是否是本地文件路径（Milvus Lite）
            if self.host.startswith("./") or self.host.endswith(".db") or "/" in self.host:
                connections.connect(alias="geo_default", uri=self.host, **keepalive_settings)
            else:
                connections.connect(alias="geo_default", host=self.host, **keepalive_settings)
            self._connected = True

    def disconnect(self):
        """断开连接"""
        if self._connected:
            connections.disconnect("geo_default")
            self._connected = False

    def create_collection(self, drop_if_exists: bool = False):
        """创建GEO Analysis Collection"""
        self.connect()

        if utility.has_collection(self.collection_name):
            if drop_if_exists:
                utility.drop_collection(self.collection_name)
            else:
                self._collection = Collection(self.collection_name)
                self._collection.load()
                return

        schema = get_geo_schema()
        self._collection = Collection(name=self.collection_name, schema=schema)

        # 创建向量索引（用于语义检索）
        index_params = {
            "metric_type": "COSINE",
            "index_type": "HNSW",
            "params": {
                "M": 16,
                "efConstruction": 200,
            },
        }
        self._collection.create_index(field_name="question_embedding", index_params=index_params)
        self._collection.load()

    def insert_single(self, result: Dict[str, Any]) -> str:
        """
        插入单条GEO分析结果

        Args:
            result: 分析结果字典

        Returns:
            插入的记录ID
        """
        if self._collection is None:
            self._collection = Collection(self.collection_name)
            self._collection.load()

        # 生成ID
        if "id" not in result:
            question_hash = hashlib.md5(result.get("question_text", "").encode()).hexdigest()[:12]
            platform = result.get("platform", "unknown")
            result["id"] = f"geo_{question_hash}_{platform}"

        # 生成问题文本的embedding向量
        question_text = result.get("question_text", "")
        embedding = self.embedding_model.embed_texts([question_text])[0]

        # 处理JSON字段
        data = [
            [result.get("id")],
            [embedding],  # question_embedding
            [result.get("block_id", "")],
            [result.get("brand_name", "")],
            [result.get("question_text", "")],
            [result.get("platform", "")],
            [result.get("mentioned", False)],
            [result.get("rank") or 0],  # handle None case
            [result.get("sentiment") or 0.0],
            [result.get("mention_count") or 0],
            [result.get("answer", "")],
            [self._to_json_str(result.get("competitors_found", []))],
            [self._to_json_str(result.get("competitor_ranks", {}))],
            [self._to_json_str(result.get("brand_citations", []))],
            [self._to_json_str(result.get("competitor_citations", {}))],
            [result.get("brand_website_cited", False)],
            [result.get("citation_authority_score") or 0.0],
            [result.get("analysis_timestamp") or int(datetime.now().timestamp())],
        ]

        self._collection.insert(data)
        self._collection.flush()
        return result.get("id")

    def insert_batch(self, results: List[Dict[str, Any]], upsert: bool = False) -> List[str]:
        """
        找量插入GEO分析结果

        Args:
            results: 分析结果列表
            upsert: 是否覆盖已存在的记录（True=覆盖，False=跳过重复）

        Returns:
            插入的记录ID列表
        """
        if self._collection is None:
            self._collection = Collection(self.collection_name)
            self._collection.load()

        ids = []
        data = []

        # 收集所有问题文本用于批量embedding
        question_texts = [result.get("question_text", "") for result in results]
        embeddings = self.embedding_model.embed_texts(question_texts)

        for idx, result in enumerate(results):
            # 生成ID
            if "id" not in result:
                question_hash = hashlib.md5(result.get("question_text", "").encode()).hexdigest()[:12]
                platform = result.get("platform", "unknown")
                result["id"] = f"geo_{question_hash}_{platform}"
            ids.append(result.get("id"))

            data.append([
                result.get("id", ""),
                embeddings[idx],  # question_embedding
                result.get("block_id", ""),
                result.get("brand_name", ""),
                result.get("question_text", ""),
                result.get("platform", ""),
                result.get("mentioned", False),
                result.get("rank") or 0,  # handle None case
                result.get("sentiment") or 0.0,
                result.get("mention_count") or 0,
                result.get("answer", ""),
                self._to_json_str(result.get("competitors_found", [])),
                self._to_json_str(result.get("competitor_ranks", {})),
                self._to_json_str(result.get("brand_citations", [])),
                self._to_json_str(result.get("competitor_citations", {})),
                result.get("brand_website_cited", False),
                result.get("citation_authority_score") or 0.0,
                result.get("analysis_timestamp") or int(datetime.now().timestamp()),
            ])

        # 转换为列格式
        if data:
            columns = [list(col) for col in zip(*data)]
            if upsert:
                self._collection.upsert(columns)
            else:
                self._collection.insert(columns)
            self._collection.flush()

        return ids

    def query_by_block(self, block_id: str) -> List[Dict]:
        """
        查询指定文本块的GEO分析结果

        Args:
            block_id: 文本块ID

        Returns:
            分析结果列表
        """
        if self._collection is None:
            self._collection = Collection(self.collection_name)
            self._collection.load()

        expr = f"block_id == '{block_id}'"
        results = self._collection.query(
            expr=expr,
            output_fields=GEOAnalysisSchema.get_all_fields(),
        )

        return [self._parse_result(r) for r in results]

    def query_by_platform(self, platform: str, brand_name: str = None) -> List[Dict]:
        """
        查询指定平台的GEO分析结果

        Args:
            platform: AI平台
            brand_name: 可选品牌过滤

        Returns:
            分析结果列表
        """
        if self._collection is None:
            self._collection = Collection(self.collection_name)
            self._collection.load()

        if brand_name:
            expr = f"platform == '{platform}' and brand_name == '{brand_name}'"
        else:
            expr = f"platform == '{platform}'"

        results = self._collection.query(
            expr=expr,
            output_fields=GEOAnalysisSchema.get_all_fields(),
            limit=10000,
        )

        return [self._parse_result(r) for r in results]

    def get_platform_stats(self, platform: str, brand_name: str) -> Dict:
        """
        获取指定平台的统计信息

        Args:
            platform: AI平台
            brand_name: 品牌名称

        Returns:
            统计信息字典
        """
        results = self.query_by_platform(platform, brand_name)

        mentioned_count = sum(1 for r in results if r.get("mentioned"))
        total_count = len(results)

        ranks = [r.get("rank") for r in results if r.get("mentioned") and r.get("rank", 0) > 0]
        avg_rank = sum(ranks) / len(ranks) if ranks else 0

        sentiments = [r.get("sentiment", 0) for r in results]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

        authority_scores = [r.get("citation_authority_score", 0) for r in results]
        avg_authority = sum(authority_scores) / len(authority_scores) if authority_scores else 0

        return {
            "mentioned_count": mentioned_count,
            "total_count": total_count,
            "avg_rank": avg_rank,
            "avg_sentiment": avg_sentiment,
            "authority_avg": avg_authority,
        }

    def _to_json_str(self, value: Any) -> str:
        """转换为JSON字符串"""
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False) if value else ""

    def _parse_result(self, result: Dict) -> Dict:
        """解析查询结果"""
        return {
            "id": result.get("id"),
            "block_id": result.get("block_id"),
            "brand_name": result.get("brand_name"),
            "question_text": result.get("question_text"),
            "platform": result.get("platform"),
            "mentioned": result.get("mentioned"),
            "rank": result.get("rank"),
            "sentiment": result.get("sentiment"),
            "mention_count": result.get("mention_count"),
            "answer": result.get("answer"),
            "competitors_found": self._parse_json_field(result.get("competitors_found")),
            "competitor_ranks": self._parse_json_field(result.get("competitor_ranks")),
            "brand_citations": self._parse_json_field(result.get("brand_citations")),
            "competitor_citations": self._parse_json_field(result.get("competitor_citations")),
            "brand_website_cited": result.get("brand_website_cited"),
            "citation_authority_score": result.get("citation_authority_score"),
            "analysis_timestamp": result.get("analysis_timestamp"),
        }

    def _parse_json_field(self, value: str) -> Any:
        """解析JSON字段"""
        if not value:
            return []
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []


def get_geo_client(collection_name: str) -> GEOAnalysisClient:
    """
    获取GEO Analysis客户端

    Args:
        collection_name: Collection名称

    Returns:
        GEOAnalysisClient实例
    """
    return GEOAnalysisClient(collection_name)