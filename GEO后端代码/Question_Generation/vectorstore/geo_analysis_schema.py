"""
GEO Analysis Schema

GEO分析详细结果Collection的Schema定义
每个问题独立存储一条记录，所有问题同等对待，不区分主问题/改写问题
"""

from pymilvus import FieldSchema, DataType, CollectionSchema
from config.geo_config import GEO_ANSWER_MAX_LENGTH
from typing import List


class GEOAnalysisSchema:
    """
    GEO Analysis Collection Schema

    存储每个问题的每个平台分析结果
    """

    @staticmethod
    def get_fields() -> List[FieldSchema]:
        """
        获取Schema字段列表

        Returns:
            FieldSchema列表
        """
        return [
            # 主键: geo_{question_hash}_{platform}
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=150),

            # === 问题文本向量字段（用于语义检索） ===
            FieldSchema(name="question_embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),
            # 基于question_text生成的embedding向量

            # === 关联信息 ===
            FieldSchema(name="block_id", dtype=DataType.VARCHAR, max_length=100),
            # 关联到文本块

            FieldSchema(name="brand_name", dtype=DataType.VARCHAR, max_length=100),
            # 品牌名称

            FieldSchema(name="question_text", dtype=DataType.VARCHAR, max_length=500),
            # 问题文本（不区分主问题/改写问题）

            # === 平台信息 ===
            FieldSchema(name="platform", dtype=DataType.VARCHAR, max_length=50),
            # AI平台: deepseek, qwen, kimi, doubao, yuanbao

            # === 分析结果 ===
            FieldSchema(name="mentioned", dtype=DataType.BOOL),
            # 品牌是否被提及

            FieldSchema(name="rank", dtype=DataType.INT64),
            # 排名位置（1=第一提及，0=未提及）

            FieldSchema(name="sentiment", dtype=DataType.FLOAT),
            # 情感评分 (-1.0 ~ 1.0)

            FieldSchema(name="mention_count", dtype=DataType.INT64),
            # 提及次数

            FieldSchema(name="answer", dtype=DataType.VARCHAR, max_length=GEO_ANSWER_MAX_LENGTH),
            # AI完整回复

            # === 竞品信息 ===
            FieldSchema(name="competitors_found", dtype=DataType.VARCHAR, max_length=500),
            # JSON字符串: 发现的竞品列表

            FieldSchema(name="competitor_ranks", dtype=DataType.VARCHAR, max_length=500),
            # JSON字符串: 竞品排名

            # === 引用信息 ===
            FieldSchema(name="brand_citations", dtype=DataType.VARCHAR, max_length=1000),
            # JSON字符串: 品牌引用列表

            FieldSchema(name="competitor_citations", dtype=DataType.VARCHAR, max_length=1000),
            # JSON字符串: 竞品引用列表

            FieldSchema(name="brand_website_cited", dtype=DataType.BOOL),
            # 品牌官网是否被引用

            FieldSchema(name="citation_authority_score", dtype=DataType.FLOAT),
            # 引用权威度评分

            # === 时间戳 ===
            FieldSchema(name="analysis_timestamp", dtype=DataType.INT64),
            # 分析时间戳
        ]

    @staticmethod
    def get_collection_schema(
        description: str = "GEO Analysis Results - All questions equally treated"
    ) -> CollectionSchema:
        """
        获取完整的Collection Schema

        Args:
            description: Collection描述

        Returns:
            CollectionSchema对象
        """
        fields = GEOAnalysisSchema.get_fields()
        return CollectionSchema(fields=fields, description=description)

    @staticmethod
    def get_all_fields() -> List[str]:
        """
        获取所有字段名列表

        Returns:
            字段名列表
        """
        return [
            "id",
            "question_embedding",
            "block_id",
            "brand_name",
            "question_text",
            "platform",
            "mentioned",
            "rank",
            "sentiment",
            "mention_count",
            "answer",
            "competitors_found",
            "competitor_ranks",
            "brand_citations",
            "competitor_citations",
            "brand_website_cited",
            "citation_authority_score",
            "analysis_timestamp",
        ]


def get_geo_schema() -> CollectionSchema:
    """
    获取GEO Analysis Schema

    Returns:
        CollectionSchema对象
    """
    return GEOAnalysisSchema.get_collection_schema()