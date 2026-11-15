"""知识图谱Schema定义: 定义实体类型、关系类型和数据结构; 支持通用的品牌推荐问题生成系统（不限定特定品牌）"""
from typing import TypedDict, List, Dict, Optional
from enum import Enum
import json
from pathlib import Path

class EntityType(Enum):
    """实体类型枚举"""
    PRODUCT = "产品"              # 具体产品名称
    BRAND = "品牌"                # 品牌名称
    EFFECT = "功效"               # 产品功效
    USAGE = "用法"                # 使用方法
    DISEASE = "疾病"              # 适用疾病/场景
    PERSON = "人物"               # 相关人物
    ORGANIZATION = "机构"         # 相关机构
    LOCATION = "地点"             # 地理位置信息
    TIME = "时间"                 # 时间信息
    CERTIFICATION = "认证"        # 资质认证
    CHANNEL = "渠道"              # 销售渠道
    CONTRAINDICATION = "禁忌"     # 使用禁忌
    COMPONENT = "成分"            # 产品成分
    PRICE = "价格"                # 价格信息
    STORAGE = "存储"              # 存储方法

class RelationType(Enum):
    """关系类型枚举"""
    HAS_EFFECT = "具有功效"               # 产品-功效
    USED_FOR = "适用于"                   # 产品-疾病/场景
    CONTRAINDICATED_FOR = "禁用于"        # 产品-人群
    PRODUCED_BY = "由...生产"             # 产品-品牌/机构
    CREATED_BY = "由...创制"              # 品牌-人物
    LOCATED_IN = "位于"                   # 机构-地点
    HAS_CERTIFICATION = "拥有认证"        # 品牌/机构-认证
    SOLD_THROUGH = "通过...销售"          # 产品-渠道
    BELONGS_TO = "属于"                   # 产品-品牌
    HAS_VARIANT = "有变种形式"            # 品牌-产品变体
    HAS_COMPONENT = "含有成分"            # 产品-成分
    STORED_AT = "存储于"                  # 产品-存储条件
    PRICE_IS = "价格为"                   # 产品-价格
    CREATED_AT = "创建于"                 # 品牌/产品-时间
    USED_BY = "被使用于"                  # 产品-人群

class KGEntity(TypedDict):
    """知识图谱实体"""
    entity_id: str               # 实体ID: "entity_001"
    entity_type: str             # 实体类型（EntityType的value）
    entity_name: str             # 实体名称
    entity_aliases: List[str]    # 实体别名（仅手动配置，不自动生成）
    confidence: float            # 抽取置信度: 0.0-1.0
    source_doc_id: str           # 来源文档ID
    properties: Dict             # 实体属性

class KGRelation(TypedDict):
    """知识图谱关系"""
    relation_id: str             # 关系ID: "rel_001"
    relation_type: str           # 关系类型（RelationType的value）
    head_entity: str             # 头实体名称
    tail_entity: str             # 尾实体名称
    confidence: float            # 抽取置信度: 0.0-1.0
    evidence: str                # 证据文本
    source_doc_id: str           # 来源文档ID

class KGTriple(TypedDict):
    """知识图谱三元组"""
    head: str                    # 头实体名称
    relation: str                # 关系类型
    tail: str                    # 尾实体名称
    confidence: float            # 置信度
    source: str                  # 来源文档ID

class KGDocument(TypedDict):
    """知识图谱文档"""
    doc_id: str
    content: str
    entities: List[KGEntity]
    relations: List[KGRelation]
    triples: List[KGTriple]
    extraction_confidence: float

# 别名管理器（从外部配置文件加载）
_alias_cache: Dict[str, Dict] = {}  # brand_name -> aliases config
def load_aliases(brand_name: str, alias_config_path: str = "data/aliases") -> Dict[str, Dict[str, List[str]]]:
    """加载指定品牌的别名配置, Args: brand_name: 品牌名称 lias_config_path: 别名配置文件目录路径; Returns: 别名配置字典 {entity_type: {entity_name: [aliases]}}"""
    if brand_name in _alias_cache:
        return _alias_cache[brand_name]

    config_file = Path(alias_config_path) / f"{brand_name}_aliases.json"
    if not config_file.exists():
        _alias_cache[brand_name] = {}
        return {}

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            aliases = json.load(f)
        _alias_cache[brand_name] = aliases
        return aliases
    except Exception as e:
        print(f"[WARN] Failed to load aliases for {brand_name}: {e}")
        _alias_cache[brand_name] = {}
        return {}

def get_aliases(brand_name: str, entity_type: str, entity_name: str, alias_config_path: str = "data/aliases") -> List[str]:
    """
    获取指定实体的别名列表 Args: brand_name: 品牌名称 entity_type: 实体类型 entity_name: 实体名称 alias_config_path: 别名配置文件目录路径
    Returns: 别名列表（如无配置则返回空列表）
    """
    aliases_config = load_aliases(brand_name, alias_config_path)

    if entity_type in aliases_config:
        type_aliases = aliases_config[entity_type]
        if entity_name in type_aliases:
            return type_aliases[entity_name]

    return []