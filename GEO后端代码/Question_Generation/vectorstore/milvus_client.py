"""
Milvus向量数据库客户端

主要功能：
- insert_texts(): 简单插入（无元数据）
- insert_with_metadata(): 带KG元数据的插入（自动生成增强文本）
"""

import json
from typing import List, Optional, Dict, Any
from pymilvus import connections, Collection, utility
from config.settings import settings
from .embedding import EmbeddingModel
from .milvus_schema import get_schema, MilvusSchema


class MilvusClient:
    """
    Milvus向量数据库客户端

    支持多源知识库的存储和检索
    统一使用v2 schema（包含完整元数据）
    """

    def __init__(
        self,
        collection_name: str = None,
        host: str = None,
        port: str = None,
    ):
        self.host = host or settings.milvus.host
        self.port = port or settings.milvus.port
        self.collection_name = collection_name
        self._collection: Optional[Collection] = None
        self._connected = False
        self.embedding_model = EmbeddingModel()

    def connect(self):
        """连接到Milvus服务器（支持Milvus Lite本地文件路径）"""
        if not self._connected:
            # keepalive设置（避免too_many_pings警告）
            # 设置心跳间隔为60秒，超时为20秒
            keepalive_settings = {
                "keepalive_interval_ms": 60000,  # 心跳间隔60秒
                "keepalive_timeout_ms": 20000,   # 心跳超时20秒
            }

            # 检查是否是本地文件路径（Milvus Lite）
            if self.host.startswith('./') or self.host.endswith('.db') or '/' in self.host:
                # Milvus Lite: 使用本地文件路径
                connections.connect(
                    alias="default",
                    uri=self.host,
                    **keepalive_settings,
                )
            else:
                # 标准Milvus: 使用host和port
                connections.connect(
                    alias="default",
                    host=self.host,
                    port=self.port,
                    **keepalive_settings,
                )
            self._connected = True

    def disconnect(self):
        """断开连接"""
        if self._connected:
            connections.disconnect("default")
            self._connected = False

    def create_collection(
        self,
        embedding_dim: int = None,
        drop_if_exists: bool = False,
    ):
        """
        创建Collection（统一使用v2 schema）

        Args:
            embedding_dim: 向量维度
            drop_if_exists: 如果已存在是否删除重建（默认False，支持增量插入）
        """
        self.connect()

        dim = embedding_dim or settings.milvus.embedding_dim

        # 检查是否已存在
        if utility.has_collection(self.collection_name):
            if drop_if_exists:
                utility.drop_collection(self.collection_name)
            else:
                # 增量模式：直接加载已有Collection
                self._collection = Collection(self.collection_name)
                self._collection.load()
                return

        # 创建新Collection（统一使用v2 schema）
        schema = get_schema(dim)
        self._collection = Collection(name=self.collection_name, schema=schema)

        # 创建向量索引（使用HNSW索引，更适合高维向量搜索）
        index_params = {
            "metric_type": "COSINE",
            "index_type": "HNSW",
            "params": {
                "M": 16,               # 每个节点的最大连接数，影响召回率
                "efConstruction": 200, # 构建时的搜索范围，影响构建质量
            },
        }
        self._collection.create_index(field_name="embedding", index_params=index_params)
        self._collection.load()

    def insert_texts(self, texts: List[str], ids: List[str]) -> bool:
        """
        插入文本（无元数据时使用空值填充）

        Args:
            texts: 文本列表
            ids: ID列表

        Returns:
            是否成功
        """
        self.connect()
        if self._collection is None:
            self._collection = Collection(self.collection_name)
        self._collection.load()

        embeddings = self.embedding_model.embed_texts(texts)

        # 构建数据（v2 schema格式，无KG信息时原始文本和增强文本相同）
        empty_metadata = self._build_empty_metadata(len(texts))
        data = [
            ids,
            texts,  # original_content: 原始文本
            texts,  # content: 无KG信息时与原始相同
            embeddings,
            *empty_metadata,
        ]

        self._collection.insert(data)
        self._collection.flush()
        return True

    def _build_empty_metadata(self, count: int) -> List:
        """
        构建空的元数据列表（用于v2 schema兼容，包含所有43字段）

        Args:
            count: 数量

        Returns:
            空元数据字段列表（39个字段：13基础 + 26 GEO）
        """
        return [
            # 基础元数据字段（13个）
            [""] * count,  # source_type
            [""] * count,  # source_url
            [""] * count,  # source_title
            [0] * count,   # source_date
            [""] * count,  # entity_tags
            [""] * count,  # relation_types
            [0.0] * count, # kg_confidence
            [""] * count,  # category
            [""] * count,  # keywords
            [0.0] * count, # quality_score
            [0] * count,   # crawl_timestamp
            [""] * count,  # brand_name
            [""] * count,  # doc_id
            # GEO字段（26个）
            [""] * count,  # generated_questions
            [0] * count,   # question_count
            ["pending"] * count,  # geo_analysis_status
            [0] * count,   # geo_total_analyses
            [0] * count,   # geo_deepseek_mentioned_count
            [0.0] * count, # geo_deepseek_avg_rank
            [0.0] * count, # geo_deepseek_avg_sentiment
            [0.0] * count, # geo_deepseek_authority_avg
            [0] * count,   # geo_qwen_mentioned_count
            [0.0] * count, # geo_qwen_avg_rank
            [0.0] * count, # geo_qwen_avg_sentiment
            [0.0] * count, # geo_qwen_authority_avg
            [0] * count,   # geo_kimi_mentioned_count
            [0.0] * count, # geo_kimi_avg_rank
            [0.0] * count, # geo_kimi_avg_sentiment
            [0.0] * count, # geo_kimi_authority_avg
            [0] * count,   # geo_doubao_mentioned_count
            [0.0] * count, # geo_doubao_avg_rank
            [0.0] * count, # geo_doubao_avg_sentiment
            [0.0] * count, # geo_doubao_authority_avg
            [0] * count,   # geo_yuanbao_mentioned_count
            [0.0] * count, # geo_yuanbao_avg_rank
            [0.0] * count, # geo_yuanbao_avg_sentiment
            [0.0] * count, # geo_yuanbao_authority_avg
            [""] * count,  # geo_competitor_summary
            [0] * count,   # geo_analysis_timestamp
        ]

    def insert_with_metadata(
        self,
        texts: List[str],
        ids: List[str],
        metadata: List[Dict[str, Any]],
    ) -> bool:
        """
        插入带元数据的文本（支持KG增强向量）

        Args:
            texts: 原始文本列表
            ids: ID列表
            metadata: 元数据列表，每个元素是一个字典，包含以下字段：
                - source_type: 来源类型
                - source_url: 来源URL
                - source_title: 来源标题
                - source_date: 发布时间戳
                - entity_tags: 实体标签列表（用于增强向量）
                - relation_types: 关系类型列表（用于增强向量）
                - kg_confidence: KG置信度
                - category: 内容分类
                - keywords: 关键词列表（用于增强向量）
                - quality_score: 质量评分
                - crawl_timestamp: 爬取时间戳
                - brand_name: 品牌名称
                - doc_id: 文档ID

        Returns:
            是否成功
        """
        self.connect()
        if self._collection is None:
            self._collection = Collection(self.collection_name)
        self._collection.load()

        # 生成KG增强文本（原始文本 + KG信息）
        enhanced_texts = []
        for text, m in zip(texts, metadata):
            enhanced_text = self._build_enhanced_text(text, m)
            enhanced_texts.append(enhanced_text)

        # 使用增强文本生成向量（包含KG信息）
        embeddings = self.embedding_model.embed_texts(enhanced_texts)

        # 处理元数据
        processed_metadata = []
        for m in metadata:
            processed_metadata.append(self._process_metadata(m))

        # 构建插入数据（按schema字段顺序）
        # id, original_content, content, embedding, source_type, ..., geo_*字段
        data = [
            ids,
            texts,  # original_content: 原始文本
            enhanced_texts,  # content: KG增强文本
            embeddings,
            # 基础元数据字段（13个）
            [m.get("source_type", "") for m in processed_metadata],
            [m.get("source_url", "") for m in processed_metadata],
            [m.get("source_title", "") for m in processed_metadata],
            [m.get("source_date", 0) for m in processed_metadata],
            [m.get("entity_tags", "") for m in processed_metadata],
            [m.get("relation_types", "") for m in processed_metadata],
            [m.get("kg_confidence", 0.0) for m in processed_metadata],
            [m.get("category", "") for m in processed_metadata],
            [m.get("keywords", "") for m in processed_metadata],
            [m.get("quality_score", 0.0) for m in processed_metadata],
            [m.get("crawl_timestamp", 0) for m in processed_metadata],
            [m.get("brand_name", "") for m in processed_metadata],
            [m.get("doc_id", "") for m in processed_metadata],
            # GEO字段（26个，默认值）
            [m.get("generated_questions", "") for m in processed_metadata],
            [m.get("question_count", 0) for m in processed_metadata],
            [m.get("geo_analysis_status", "pending") for m in processed_metadata],
            [m.get("geo_total_analyses", 0) for m in processed_metadata],
            [m.get("geo_deepseek_mentioned_count", 0) for m in processed_metadata],
            [m.get("geo_deepseek_avg_rank", 0.0) for m in processed_metadata],
            [m.get("geo_deepseek_avg_sentiment", 0.0) for m in processed_metadata],
            [m.get("geo_deepseek_authority_avg", 0.0) for m in processed_metadata],
            [m.get("geo_qwen_mentioned_count", 0) for m in processed_metadata],
            [m.get("geo_qwen_avg_rank", 0.0) for m in processed_metadata],
            [m.get("geo_qwen_avg_sentiment", 0.0) for m in processed_metadata],
            [m.get("geo_qwen_authority_avg", 0.0) for m in processed_metadata],
            [m.get("geo_kimi_mentioned_count", 0) for m in processed_metadata],
            [m.get("geo_kimi_avg_rank", 0.0) for m in processed_metadata],
            [m.get("geo_kimi_avg_sentiment", 0.0) for m in processed_metadata],
            [m.get("geo_kimi_authority_avg", 0.0) for m in processed_metadata],
            [m.get("geo_doubao_mentioned_count", 0) for m in processed_metadata],
            [m.get("geo_doubao_avg_rank", 0.0) for m in processed_metadata],
            [m.get("geo_doubao_avg_sentiment", 0.0) for m in processed_metadata],
            [m.get("geo_doubao_authority_avg", 0.0) for m in processed_metadata],
            [m.get("geo_yuanbao_mentioned_count", 0) for m in processed_metadata],
            [m.get("geo_yuanbao_avg_rank", 0.0) for m in processed_metadata],
            [m.get("geo_yuanbao_avg_sentiment", 0.0) for m in processed_metadata],
            [m.get("geo_yuanbao_authority_avg", 0.0) for m in processed_metadata],
            [m.get("geo_competitor_summary", "") for m in processed_metadata],
            [m.get("geo_analysis_timestamp", 0) for m in processed_metadata],
        ]

        self._collection.insert(data)
        self._collection.flush()
        return True

    def _build_enhanced_text(self, original_text: str, metadata: Dict[str, Any]) -> str:
        """
        构建KG增强文本

        格式：原始文本。【实体：A，B；关系：R1，R2；标签：T1，T2】

        Args:
            original_text: 原始文本
            metadata: 元数据（包含entity_tags, relation_types, keywords等）

        Returns:
            增强后的文本
        """
        # 提取KG信息
        entity_tags = metadata.get("entity_tags", [])
        relation_types = metadata.get("relation_types", [])
        keywords = metadata.get("keywords", [])
        category = metadata.get("category", "")

        # 构建KG信息字符串
        kg_parts = []

        if entity_tags:
            entities_str = ", ".join(entity_tags[:10])  # 最多10个实体
            kg_parts.append(f"实体：{entities_str}")

        if relation_types:
            relations_str = ", ".join(relation_types[:10])  # 最多10个关系
            kg_parts.append(f"关系：{relations_str}")

        if keywords:
            keywords_str = ", ".join(keywords[:10])  # 最多10个关键词
            kg_parts.append(f"关键词：{keywords_str}")

        if category:
            kg_parts.append(f"分类：{category}")

        # 拼接增强文本
        if kg_parts:
            kg_info = "【" + "；".join(kg_parts) + "】"
            enhanced_text = f"{original_text} {kg_info}"
        else:
            enhanced_text = original_text

        return enhanced_text

    def _process_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理元数据，将列表转换为JSON字符串

        Args:
            metadata: 原始元数据

        Returns:
            处理后的元数据（包含所有Schema字段）
        """
        import json

        processed = {}

        # 处理列表字段（转换为JSON字符串）
        for field in ["entity_tags", "relation_types", "keywords"]:
            value = metadata.get(field, [])
            if isinstance(value, list):
                processed[field] = json.dumps(value, ensure_ascii=False)
            else:
                processed[field] = value if value else ""

        # 处理其他基础字段
        processed["source_type"] = metadata.get("source_type", "")
        processed["source_url"] = metadata.get("source_url", "")
        processed["source_title"] = metadata.get("source_title", "")
        processed["source_date"] = metadata.get("source_date", 0)
        processed["kg_confidence"] = metadata.get("kg_confidence", 0.0)
        processed["category"] = metadata.get("category", "")
        processed["quality_score"] = metadata.get("quality_score", 0.0)
        processed["crawl_timestamp"] = metadata.get("crawl_timestamp", 0)
        processed["brand_name"] = metadata.get("brand_name", "")
        processed["doc_id"] = metadata.get("doc_id", "")

        # 处理GEO字段（使用默认值）
        processed["generated_questions"] = metadata.get("generated_questions", "")
        processed["question_count"] = metadata.get("question_count", 0)
        processed["geo_analysis_status"] = metadata.get("geo_analysis_status", "pending")
        processed["geo_total_analyses"] = metadata.get("geo_total_analyses", 0)
        processed["geo_deepseek_mentioned_count"] = metadata.get("geo_deepseek_mentioned_count", 0)
        processed["geo_deepseek_avg_rank"] = metadata.get("geo_deepseek_avg_rank", 0.0)
        processed["geo_deepseek_avg_sentiment"] = metadata.get("geo_deepseek_avg_sentiment", 0.0)
        processed["geo_deepseek_authority_avg"] = metadata.get("geo_deepseek_authority_avg", 0.0)
        processed["geo_qwen_mentioned_count"] = metadata.get("geo_qwen_mentioned_count", 0)
        processed["geo_qwen_avg_rank"] = metadata.get("geo_qwen_avg_rank", 0.0)
        processed["geo_qwen_avg_sentiment"] = metadata.get("geo_qwen_avg_sentiment", 0.0)
        processed["geo_qwen_authority_avg"] = metadata.get("geo_qwen_authority_avg", 0.0)
        processed["geo_kimi_mentioned_count"] = metadata.get("geo_kimi_mentioned_count", 0)
        processed["geo_kimi_avg_rank"] = metadata.get("geo_kimi_avg_rank", 0.0)
        processed["geo_kimi_avg_sentiment"] = metadata.get("geo_kimi_avg_sentiment", 0.0)
        processed["geo_kimi_authority_avg"] = metadata.get("geo_kimi_authority_avg", 0.0)
        processed["geo_doubao_mentioned_count"] = metadata.get("geo_doubao_mentioned_count", 0)
        processed["geo_doubao_avg_rank"] = metadata.get("geo_doubao_avg_rank", 0.0)
        processed["geo_doubao_avg_sentiment"] = metadata.get("geo_doubao_avg_sentiment", 0.0)
        processed["geo_doubao_authority_avg"] = metadata.get("geo_doubao_authority_avg", 0.0)
        processed["geo_yuanbao_mentioned_count"] = metadata.get("geo_yuanbao_mentioned_count", 0)
        processed["geo_yuanbao_avg_rank"] = metadata.get("geo_yuanbao_avg_rank", 0.0)
        processed["geo_yuanbao_avg_sentiment"] = metadata.get("geo_yuanbao_avg_sentiment", 0.0)
        processed["geo_yuanbao_authority_avg"] = metadata.get("geo_yuanbao_authority_avg", 0.0)
        processed["geo_competitor_summary"] = metadata.get("geo_competitor_summary", "")
        processed["geo_analysis_timestamp"] = metadata.get("geo_analysis_timestamp", 0)

        return processed

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        获取Collection统计信息

        Returns:
            统计信息字典
        """
        self.connect()
        if self._collection is None:
            self._collection = Collection(self.collection_name)
        self._collection.load()

        stats = {
            "collection_name": self.collection_name,
            "num_entities": self._collection.num_entities,
        }

        return stats

    def get_collection(self) -> Collection:
        """获取Collection对象"""
        self.connect()
        if self._collection is None:
            self._collection = Collection(self.collection_name)
        return self._collection

    def delete_by_ids(self, ids: List[str]) -> bool:
        """
        按ID删除数据

        Args:
            ids: ID列表

        Returns:
            是否成功
        """
        self.connect()
        if self._collection is None:
            self._collection = Collection(self.collection_name)
        self._collection.load()

        id_list = ", ".join([f"'{i}'" for i in ids])
        expr = f"id in [{id_list}]"
        self._collection.delete(expr)
        self._collection.flush()
        return True

    def delete_by_brand(self, brand_name: str) -> bool:
        """
        按品牌删除数据

        Args:
            brand_name: 品牌名称

        Returns:
            是否成功
        """
        self.connect()
        if self._collection is None:
            self._collection = Collection(self.collection_name)
        self._collection.load()

        expr = f"brand_name == '{brand_name}'"
        self._collection.delete(expr)
        self._collection.flush()
        return True

    def delete_by_source_type(self, source_type: str, brand_name: str = None) -> Dict:
        """
        按来源类型删除文档

        Args:
            source_type: 来源类型 (official_site, zhihu, xiaohongshu, whitepaper, pdf, json)
            brand_name: 可选品牌过滤

        Returns:
            {"deleted_count": N, "success": True/False}
        """
        self.connect()
        if self._collection is None:
            self._collection = Collection(self.collection_name)
        self._collection.load()

        # 构建过滤表达式
        if brand_name:
            expr = f"source_type == '{source_type}' and brand_name == '{brand_name}'"
        else:
            expr = f"source_type == '{source_type}'"

        # 获取删除前的数量
        query_result = self._collection.query(
            expr=expr,
            output_fields=["id"],
        )
        deleted_count = len(query_result)

        # 执行删除
        self._collection.delete(expr)
        self._collection.flush()

        return {
            "deleted_count": deleted_count,
            "success": True,
        }

    def delete_by_source_url(self, source_url: str, brand_name: str = None) -> Dict:
        """
        按来源URL删除文档

        Args:
            source_url: 来源URL（精确匹配）
            brand_name: 可选品牌过滤

        Returns:
            {"deleted_count": N, "success": True/False, "deleted_doc_ids": [...]}
        """
        self.connect()
        if self._collection is None:
            self._collection = Collection(self.collection_name)
        self._collection.load()

        # 构建过滤表达式
        if brand_name:
            expr = f"source_url == '{source_url}' and brand_name == '{brand_name}'"
        else:
            expr = f"source_url == '{source_url}'"

        # 获取受影响的doc_ids
        query_result = self._collection.query(
            expr=expr,
            output_fields=["id", "doc_id"],
        )
        deleted_count = len(query_result)
        deleted_doc_ids = [r.get("doc_id") for r in query_result]

        # 执行删除
        self._collection.delete(expr)
        self._collection.flush()

        return {
            "deleted_count": deleted_count,
            "deleted_doc_ids": deleted_doc_ids,
            "success": True,
        }

    def delete_by_doc_id_prefix(self, doc_id_prefix: str, brand_name: str = None) -> Dict:
        """
        除属于父文档的所有分块

        Args:
            doc_id_prefix: 父doc_id（将删除doc_id和doc_id_block_*）
            brand_name: 可选品牌过滤

        Returns:
            {"deleted_count": N, "success": True/False, "deleted_ids": [...]}
        """
        self.connect()
        if self._collection is None:
            self._collection = Collection(self.collection_name)
        self._collection.load()

        # 构建基础过滤
        if brand_name:
            expr = f"brand_name == '{brand_name}'"
        else:
            expr = None

        # 查询所有匹配的文档
        query_result = self._collection.query(
            expr=expr,
            output_fields=["id", "doc_id"],
        )

        # 按doc_id前缀过滤
        ids_to_delete = []
        for r in query_result:
            doc_id = r.get("doc_id", "")
            # 匹配精确doc_id或分块（doc_id_block_*）
            if doc_id == doc_id_prefix or doc_id.startswith(f"{doc_id_prefix}_block_"):
                ids_to_delete.append(r.get("id"))

        if ids_to_delete:
            # 按ID删除
            id_list_str = ", ".join([f"'{id}'" for id in ids_to_delete])
            delete_expr = f"id in [{id_list_str}]"
            self._collection.delete(delete_expr)
            self._collection.flush()

        return {
            "deleted_count": len(ids_to_delete),
            "deleted_ids": ids_to_delete,
            "success": True,
        }

    def check_doc_exists(self, source_type: str, source_url: str, content_prefix: str = "") -> Dict:
        """
        检查文档是否已存在于Collection中

        Args:
            source_type: 来源类型
            source_url: 来源URL
            content_prefix: 内容前100字符（用于哈希匹配）

        Returns:
            {"exists": True/False, "existing_ids": [...], "existing_blocks": N}
        """
        self.connect()
        if self._collection is None:
            self._collection = Collection(self.collection_name)
        self._collection.load()

        # 构建预期doc_id前缀
        import hashlib
        hash_input = f"{source_url}_{content_prefix[:100]}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        expected_doc_id_prefix = f"{source_type}_{hash_value}"

        # 查询匹配的文档
        expr = f"source_type == '{source_type}' and source_url == '{source_url}'"

        query_result = self._collection.query(
            expr=expr,
            output_fields=["id", "doc_id"],
        )

        # 检查是否有匹配预期模式的doc_id
        matching_ids = []
        for doc in query_result:
            doc_id = doc.get("doc_id", "")
            if doc_id.startswith(expected_doc_id_prefix):
                matching_ids.append(doc_id)

        return {
            "exists": len(matching_ids) > 0,
            "existing_ids": matching_ids,
            "existing_blocks": len(matching_ids),
            "expected_doc_id_prefix": expected_doc_id_prefix,
        }

    def get_source_stats(self, brand_name: str = None) -> Dict:
        """
        获取按来源类型的详细统计

        Args:
            brand_name: 可选品牌过滤

        Returns:
            {
                "total_entities": N,
                "by_source_type": {"official_site": {"count": N, "avg_quality": X}, ...},
                "by_category": {...},
                "avg_quality_score": X,
            }
        """
        self.connect()
        if self._collection is None:
            self._collection = Collection(self.collection_name)
        self._collection.load()

        # 构建过滤
        expr = f"brand_name == '{brand_name}'" if brand_name else None

        # 查询所有文档的元数据
        output_fields = ["id", "source_type", "category", "quality_score",
                         "crawl_timestamp", "source_date", "source_url", "doc_id"]

        query_result = self._collection.query(
            expr=expr,
            output_fields=output_fields,
            limit=10000,
        )

        # 计算统计
        stats = {
            "total_entities": len(query_result),
            "by_source_type": {},
            "by_category": {},
            "avg_quality_score": 0.0,
        }

        total_quality = 0.0
        for doc in query_result:
            source_type = doc.get("source_type", "unknown")
            category = doc.get("category", "unknown")
            quality = doc.get("quality_score", 0.0)

            # 按来源类型统计
            if source_type not in stats["by_source_type"]:
                stats["by_source_type"][source_type] = {
                    "count": 0,
                    "total_quality": 0.0,
                    "avg_quality": 0.0,
                }
            stats["by_source_type"][source_type]["count"] += 1
            stats["by_source_type"][source_type]["total_quality"] += quality

            # 按分类统计
            if category not in stats["by_category"]:
                stats["by_category"][category] = 0
            stats["by_category"][category] += 1

            total_quality += quality

        # 计算平均值
        if stats["total_entities"] > 0:
            stats["avg_quality_score"] = total_quality / stats["total_entities"]

        for source_type in stats["by_source_type"]:
            count = stats["by_source_type"][source_type]["count"]
            if count > 0:
                stats["by_source_type"][source_type]["avg_quality"] = \
                    stats["by_source_type"][source_type]["total_quality"] / count
            # 移除total_quality
            del stats["by_source_type"][source_type]["total_quality"]

        return stats

    def query_by_filter(
        self,
        brand_name: str = None,
        source_type: str = None,
        source_url: str = None,
        category: str = None,
        min_quality: float = None,
        limit: int = 100,
        output_fields: List[str] = None,
    ) -> List[Dict]:
        """
        按过滤条件查询文档

        Args:
            brand_name: 按品牌过滤
            source_type: 按来源类型过滤
            source_url: 按来源URL过滤
            category: 按分类过滤
            min_quality: 最小质量评分
            limit: 最大结果数
            output_fields: 返回字段列表

        Returns:
            匹配文档列表
        """
        self.connect()
        if self._collection is None:
            self._collection = Collection(self.collection_name)
        self._collection.load()

        # 构建过滤表达式
        filter_parts = []

        if brand_name:
            filter_parts.append(f"brand_name == '{brand_name}'")
        if source_type:
            filter_parts.append(f"source_type == '{source_type}'")
        if source_url:
            filter_parts.append(f"source_url == '{source_url}'")
        if category:
            filter_parts.append(f"category == '{category}'")
        if min_quality:
            filter_parts.append(f"quality_score >= {min_quality}")

        expr = " and ".join(filter_parts) if filter_parts else None

        # 默认输出字段（完整内容，不含embedding向量）
        if output_fields is None:
            output_fields = [
                "id", "doc_id", "original_content", "content",
                "source_type", "source_url", "source_title", "source_date",
                "entity_tags", "relation_types", "keywords", "kg_confidence",
                "category", "quality_score", "crawl_timestamp", "brand_name"
            ]

        # 查询
        query_result = self._collection.query(
            expr=expr,
            output_fields=output_fields,
            limit=limit,
        )

        # 处理结果
        results = []
        for doc in query_result:
            result = {field: doc.get(field) for field in output_fields}
            # 解析JSON字段（支持字符串和列表）
            for field in ["entity_tags", "relation_types", "keywords"]:
                if field in output_fields:
                    result[field] = self._parse_json_field(result.get(field))
            results.append(result)

        return results

    def query_all_blocks(
        self,
        brand_name: str = None,
        offset: int = 0,
        limit: int = 1000,
        output_fields: List[str] = None,
    ) -> Dict:
        """
        遍历所有文档块（用于问题生成流程）

        Args:
            brand_name: 品牌名称过滤
            offset: 偏移量（用于分页遍历）
            limit: 每批次数量
            output_fields: 返回字段列表

        Returns:
            {
                "blocks": List[Dict],  # 文档块列表
                "total": int,          # 总数量
                "has_more": bool,      # 是否有更多数据
            }
        """
        self.connect()
        if self._collection is None:
            self._collection = Collection(self.collection_name)
        self._collection.load()

        # 构建过滤表达式
        expr = f"brand_name == '{brand_name}'" if brand_name else None

        # 默认输出字段（完整内容，不含embedding向量）
        if output_fields is None:
            output_fields = [
                "id", "doc_id", "original_content", "content",
                "source_type", "source_url", "source_title", "source_date",
                "entity_tags", "relation_types", "keywords", "kg_confidence",
                "category", "quality_score", "crawl_timestamp", "brand_name"
            ]

        # 获取总数
        stats = self.get_collection_stats()
        total = stats.get("num_entities", 0)

        # 查询（带偏移）
        query_result = self._collection.query(
            expr=expr,
            output_fields=output_fields,
            limit=limit,
            offset=offset,
        )

        # 处理结果（解析JSON字段）
        blocks = []
        for doc in query_result:
            block = {
                "id": doc.get("id"),
                "doc_id": doc.get("doc_id"),
                "original_content": doc.get("original_content"),
                "content": doc.get("content"),  # KG增强文本
                "metadata": {
                    "source_type": doc.get("source_type"),
                    "source_url": doc.get("source_url"),
                    "source_title": doc.get("source_title"),
                    "source_date": doc.get("source_date", 0),
                    "category": doc.get("category"),
                    "brand_name": doc.get("brand_name"),
                    "entity_tags": self._parse_json_field(doc.get("entity_tags")),
                    "relation_types": self._parse_json_field(doc.get("relation_types")),
                    "keywords": self._parse_json_field(doc.get("keywords")),
                    "kg_confidence": doc.get("kg_confidence", 0.0),
                    "quality_score": doc.get("quality_score", 0.0),
                    "crawl_timestamp": doc.get("crawl_timestamp", 0),
                }
            }
            blocks.append(block)

        return {
            "blocks": blocks,
            "total": total,
            "has_more": offset + len(blocks) < total,
        }


    def get_block_by_id(self, block_id: str) -> Optional[Dict]:
        """按 ID 获取单个文档块"""
        self.connect()
        if self._collection is None:
            self._collection = Collection(self.collection_name)
        self._collection.load()
        
        expr = f"id == '{block_id}'"
        output_fields = [
            "id", "doc_id", "original_content", "content",
            "entity_tags", "relation_types", "keywords",
            "source_type", "source_url", "brand_name"
        ]
        query_result = self._collection.query(
            expr=expr,
            output_fields=output_fields,
            limit=1,
        )
        
        if not query_result:
            return None
        
        doc = query_result[0]
        return {
            "id": doc.get("id"),
            "doc_id": doc.get("doc_id"),
            "original_content": doc.get("original_content", ""),
            "content": doc.get("content", ""),
            "entity_tags": self._parse_json_field(doc.get("entity_tags")),
            "relation_types": self._parse_json_field(doc.get("relation_types")),
            "keywords": self._parse_json_field(doc.get("keywords")),
        }

    def get_block_by_index(
        self,
        brand_name: str,
        index: int,
    ) -> Optional[Dict]:
        """
        按索引获取单个文档块（用于问题生成循环）

        Args:
            brand_name: 品牌名称
            index: 块索引（0-based）

        Returns:
            文档块字典或None
        """
        result = self.query_all_blocks(
            brand_name=brand_name,
            offset=index,
            limit=1,
        )
        blocks = result.get("blocks", [])
        return blocks[0] if blocks else None

    def _parse_json_field(self, value) -> List:
        """解析JSON字段（支持字符串和列表输入）"""
        if not value:
            return []
        if isinstance(value, list):
            return value  # Milvus Lite可能直接返回列表
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []

    def update_by_id(self, id: str, update_fields: Dict[str, Any]) -> bool:
        """
        按ID更新记录的字段（用于GEO分析结果更新）

        注意：Milvus不支持部分更新，需要先查询完整记录，再upsert更新

        Args:
            id: 记录ID
            update_fields: 要更新的字段字典

        Returns:
            是否成功
        """
        self.connect()
        if self._collection is None:
            self._collection = Collection(self.collection_name)
        self._collection.load()

        # 1. 查询现有记录的完整数据
        expr = f"id == '{id}'"
        existing_records = self._collection.query(
            expr=expr,
            output_fields=MilvusSchema.get_all_fields() + ["embedding"],
            limit=1,
        )

        if not existing_records:
            print(f"[WARN] Record not found: {id}")
            return False

        existing = existing_records[0]

        # 2. 合并更新字段
        merged = {}
        for field in MilvusSchema.get_all_fields() + ["embedding"]:
            if field in update_fields:
                merged[field] = update_fields[field]
            else:
                merged[field] = existing.get(field)

        # 3. 处理JSON字段（确保是字符串格式）
        for field in ["entity_tags", "relation_types", "keywords", "generated_questions", "geo_competitor_summary"]:
            if field in merged and isinstance(merged[field], list):
                merged[field] = json.dumps(merged[field], ensure_ascii=False)
            elif field in merged and isinstance(merged[field], dict):
                merged[field] = json.dumps(merged[field], ensure_ascii=False)

        # 4. 构建upsert数据（按schema字段顺序）
        # 注意：embedding字段需要特殊处理，保持原向量
        data = [
            [merged.get("id")],
            [merged.get("original_content", "")],
            [merged.get("content", "")],
            [merged.get("embedding")],  # 保持原向量
            [merged.get("source_type", "")],
            [merged.get("source_url", "")],
            [merged.get("source_title", "")],
            [merged.get("source_date", 0)],
            [merged.get("entity_tags", "")],
            [merged.get("relation_types", "")],
            [merged.get("kg_confidence", 0.0)],
            [merged.get("category", "")],
            [merged.get("keywords", "")],
            [merged.get("quality_score", 0.0)],
            [merged.get("crawl_timestamp", 0)],
            [merged.get("brand_name", "")],
            [merged.get("doc_id", "")],
            # GEO字段
            [merged.get("generated_questions", "")],
            [merged.get("question_count", 0)],
            [merged.get("geo_analysis_status", "")],
            [merged.get("geo_total_analyses", 0)],
            [merged.get("geo_deepseek_mentioned_count", 0)],
            [merged.get("geo_deepseek_avg_rank", 0.0)],
            [merged.get("geo_deepseek_avg_sentiment", 0.0)],
            [merged.get("geo_deepseek_authority_avg", 0.0)],
            [merged.get("geo_qwen_mentioned_count", 0)],
            [merged.get("geo_qwen_avg_rank", 0.0)],
            [merged.get("geo_qwen_avg_sentiment", 0.0)],
            [merged.get("geo_qwen_authority_avg", 0.0)],
            [merged.get("geo_kimi_mentioned_count", 0)],
            [merged.get("geo_kimi_avg_rank", 0.0)],
            [merged.get("geo_kimi_avg_sentiment", 0.0)],
            [merged.get("geo_kimi_authority_avg", 0.0)],
            [merged.get("geo_doubao_mentioned_count", 0)],
            [merged.get("geo_doubao_avg_rank", 0.0)],
            [merged.get("geo_doubao_avg_sentiment", 0.0)],
            [merged.get("geo_doubao_authority_avg", 0.0)],
            [merged.get("geo_yuanbao_mentioned_count", 0)],
            [merged.get("geo_yuanbao_avg_rank", 0.0)],
            [merged.get("geo_yuanbao_avg_sentiment", 0.0)],
            [merged.get("geo_yuanbao_authority_avg", 0.0)],
            [merged.get("geo_competitor_summary", "")],
            [merged.get("geo_analysis_timestamp", 0)],
        ]

        # 5. 执行upsert
        self._collection.upsert(data)
        self._collection.flush()

        return True