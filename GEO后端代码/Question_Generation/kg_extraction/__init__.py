"""
知识图谱抽取模块

主要入口：
- KGBuilder：多文档知识图谱构建
- JointKGExtractor：单文档联合抽取器
- extract_kg_jointly：单文档抽取便捷函数

辅助工具：
- filter_by_confidence：KG置信度过滤
- deduplicate_kg_items：KG去重

输入：文档列表 [{"doc_id": "...", "content": "..."}]
输出：KG数据 {
    "entities": [...],      # 实体列表
    "relations": [...],     # 关系列表
    "triples": [...],       # 三元组列表
    "documents": [...],     # 各文档KG结果
    "total_entities": N,    # 统计信息
    "total_relations": N,
    "total_triples": N,
}
"""

from .kg_schema import KGEntity, KGRelation, KGTriple, EntityType, RelationType
from .kg_builder import (
    KGBuilder,
    JointKGExtractor,
    extract_kg_jointly,
    build_knowledge_graph,
    filter_by_confidence,
    deduplicate_kg_items,
)

__all__ = [
    # 数据结构
    "KGEntity",
    "KGRelation",
    "KGTriple",
    "EntityType",
    "RelationType",
    # 主要入口
    "KGBuilder",
    "JointKGExtractor",
    "extract_kg_jointly",
    "build_knowledge_graph",
    # 辅助工具
    "filter_by_confidence",
    "deduplicate_kg_items",
]