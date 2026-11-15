"""
Milvus Schema定义

包含完整元数据支持：
- 来源信息（source_type, source_url, source_title等）
- 知识图谱信息（entity_tags, relation_types等）
- 内容分类和质量指标
- KG增强向量（original_content用于显示，content用于向量化）
"""

from pymilvus import FieldSchema, DataType, CollectionSchema
from typing import List


class MilvusSchema:
    """
    Milvus Collection Schema

    支持多源知识库的完整元数据存储
    """

    @staticmethod
    def get_fields(embedding_dim: int = 1024) -> List[FieldSchema]:
        """
        获取Schema字段列表

        Args:
            embedding_dim: 向量维度

        Returns:
            FieldSchema列表
        """
        return [
            # 主键
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),

            # 原始内容字段（用于展示，不含KG信息）
            FieldSchema(name="original_content", dtype=DataType.VARCHAR, max_length=6000),

            # 增强内容字段（用于向量化，包含KG信息）
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=8000),

            # 向量字段（基于增强内容生成）
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embedding_dim),

            # === 来源信息 ===
            FieldSchema(name="source_type", dtype=DataType.VARCHAR, max_length=50),
            # 值: "official_site", "zhihu", "xiaohongshu", "whitepaper", "manual"

            FieldSchema(name="source_url", dtype=DataType.VARCHAR, max_length=500),
            # 原始URL或文件路径

            FieldSchema(name="source_title", dtype=DataType.VARCHAR, max_length=200),
            # 来源标题

            FieldSchema(name="source_date", dtype=DataType.INT64),
            # 发布时间戳（Unix timestamp）

            # === 知识图谱信息 ===
            FieldSchema(name="entity_tags", dtype=DataType.VARCHAR, max_length=500),
            # JSON字符串格式示例: ["品牌名", "功效关键词", "适用场景"]

            FieldSchema(name="relation_types", dtype=DataType.VARCHAR, max_length=500),
            # JSON字符串格式: ["has_effect", "used_for"]

            FieldSchema(name="kg_confidence", dtype=DataType.FLOAT),
            # KG抽取置信度: 0.0-1.0

            # === 内容分类 ===
            FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=100),
            # 值: "产品介绍", "使用说明", "禁忌说明", "功效说明", "购买渠道"等

            FieldSchema(name="keywords", dtype=DataType.VARCHAR, max_length=500),
            # JSON字符串格式: 关键词列表

            # === 质量指标 ===
            FieldSchema(name="quality_score", dtype=DataType.FLOAT),
            # 内容质量评分: 0.0-1.0

            FieldSchema(name="crawl_timestamp", dtype=DataType.INT64),
            # 爬取时间戳

            # === 品牌标识 ===
            FieldSchema(name="brand_name", dtype=DataType.VARCHAR, max_length=100),
            # 品牌名称

            FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=100),
            # 原文档ID，用于追溯

            # === GEO分析相关字段（问题存储） ===
            FieldSchema(name="generated_questions", dtype=DataType.VARCHAR, max_length=6000),
            # JSON字符串: 该块生成的所有问题列表

            FieldSchema(name="question_count", dtype=DataType.INT64),
            # 问题总数（主问题+改写问题）

            # === GEO分析状态 ===
            FieldSchema(name="geo_analysis_status", dtype=DataType.VARCHAR, max_length=50),
            # pending/completed/failed

            FieldSchema(name="geo_total_analyses", dtype=DataType.INT64),
            # 总分析次数 = question_count × 5

            # === DeepSeek平台GEO统计（独立统计，不跨平台汇总） ===
            FieldSchema(name="geo_deepseek_mentioned_count", dtype=DataType.INT64),
            FieldSchema(name="geo_deepseek_avg_rank", dtype=DataType.FLOAT),
            FieldSchema(name="geo_deepseek_avg_sentiment", dtype=DataType.FLOAT),
            FieldSchema(name="geo_deepseek_authority_avg", dtype=DataType.FLOAT),

            # === 通义千问平台GEO统计 ===
            FieldSchema(name="geo_qwen_mentioned_count", dtype=DataType.INT64),
            FieldSchema(name="geo_qwen_avg_rank", dtype=DataType.FLOAT),
            FieldSchema(name="geo_qwen_avg_sentiment", dtype=DataType.FLOAT),
            FieldSchema(name="geo_qwen_authority_avg", dtype=DataType.FLOAT),

            # === Kimi平台GEO统计 ===
            FieldSchema(name="geo_kimi_mentioned_count", dtype=DataType.INT64),
            FieldSchema(name="geo_kimi_avg_rank", dtype=DataType.FLOAT),
            FieldSchema(name="geo_kimi_avg_sentiment", dtype=DataType.FLOAT),
            FieldSchema(name="geo_kimi_authority_avg", dtype=DataType.FLOAT),

            # === 豆包平台GEO统计 ===
            FieldSchema(name="geo_doubao_mentioned_count", dtype=DataType.INT64),
            FieldSchema(name="geo_doubao_avg_rank", dtype=DataType.FLOAT),
            FieldSchema(name="geo_doubao_avg_sentiment", dtype=DataType.FLOAT),
            FieldSchema(name="geo_doubao_authority_avg", dtype=DataType.FLOAT),

            # === 元宝平台GEO统计 ===
            FieldSchema(name="geo_yuanbao_mentioned_count", dtype=DataType.INT64),
            FieldSchema(name="geo_yuanbao_avg_rank", dtype=DataType.FLOAT),
            FieldSchema(name="geo_yuanbao_avg_sentiment", dtype=DataType.FLOAT),
            FieldSchema(name="geo_yuanbao_authority_avg", dtype=DataType.FLOAT),

            # === 竞品统计汇总 ===
            FieldSchema(name="geo_competitor_summary", dtype=DataType.VARCHAR, max_length=2000),
            # JSON字符串: 各竞品在各平台的提及统计

            # === GEO分析时间戳 ===
            FieldSchema(name="geo_analysis_timestamp", dtype=DataType.INT64),
        ]

    @staticmethod
    def get_collection_schema(
        embedding_dim: int = 1024,
        description: str = "Knowledge Base with Metadata"
    ) -> CollectionSchema:
        """
        获取完整的Collection Schema

        Args:
            embedding_dim: 向量维度
            description: Collection描述

        Returns:
            CollectionSchema对象
        """
        fields = MilvusSchema.get_fields(embedding_dim)
        return CollectionSchema(fields=fields, description=description)

    @staticmethod
    def get_metadata_fields() -> List[str]:
        """
        获取元数据字段名列表（不含id, original_content, content, embedding）

        Returns:
            元数据字段名列表
        """
        return [
            "source_type",
            "source_url",
            "source_title",
            "source_date",
            "entity_tags",
            "relation_types",
            "kg_confidence",
            "category",
            "keywords",
            "quality_score",
            "crawl_timestamp",
            "brand_name",
            "doc_id",
            # GEO相关字段
            "generated_questions",
            "question_count",
            "geo_analysis_status",
            "geo_total_analyses",
            "geo_deepseek_mentioned_count",
            "geo_deepseek_avg_rank",
            "geo_deepseek_avg_sentiment",
            "geo_deepseek_authority_avg",
            "geo_qwen_mentioned_count",
            "geo_qwen_avg_rank",
            "geo_qwen_avg_sentiment",
            "geo_qwen_authority_avg",
            "geo_kimi_mentioned_count",
            "geo_kimi_avg_rank",
            "geo_kimi_avg_sentiment",
            "geo_kimi_authority_avg",
            "geo_doubao_mentioned_count",
            "geo_doubao_avg_rank",
            "geo_doubao_avg_sentiment",
            "geo_doubao_authority_avg",
            "geo_yuanbao_mentioned_count",
            "geo_yuanbao_avg_rank",
            "geo_yuanbao_avg_sentiment",
            "geo_yuanbao_authority_avg",
            "geo_competitor_summary",
            "geo_analysis_timestamp",
        ]

    @staticmethod
    def get_geo_fields() -> List[str]:
        """
        获取GEO分析相关字段名列表

        Returns:
            GEO字段名列表
        """
        return [
            "generated_questions",
            "question_count",
            "geo_analysis_status",
            "geo_total_analyses",
            "geo_deepseek_mentioned_count",
            "geo_deepseek_avg_rank",
            "geo_deepseek_avg_sentiment",
            "geo_deepseek_authority_avg",
            "geo_qwen_mentioned_count",
            "geo_qwen_avg_rank",
            "geo_qwen_avg_sentiment",
            "geo_qwen_authority_avg",
            "geo_kimi_mentioned_count",
            "geo_kimi_avg_rank",
            "geo_kimi_avg_sentiment",
            "geo_kimi_authority_avg",
            "geo_doubao_mentioned_count",
            "geo_doubao_avg_rank",
            "geo_doubao_avg_sentiment",
            "geo_doubao_authority_avg",
            "geo_yuanbao_mentioned_count",
            "geo_yuanbao_avg_rank",
            "geo_yuanbao_avg_sentiment",
            "geo_yuanbao_authority_avg",
            "geo_competitor_summary",
            "geo_analysis_timestamp",
        ]

    @staticmethod
    def get_all_fields() -> List[str]:
        """
        获取所有字段名列表（包括id, original_content, content）

        Returns:
            所有字段名列表
        """
        return ["id", "original_content", "content", "embedding"] + MilvusSchema.get_metadata_fields()


def get_schema(embedding_dim: int = 1024) -> CollectionSchema:
    """
    获取Schema

    Args:
        embedding_dim: 向量维度

    Returns:
        CollectionSchema对象
    """
    return MilvusSchema.get_collection_schema(embedding_dim)