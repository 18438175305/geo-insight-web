"""
GEO 追踪分析配置

包含：
- 引用源分类规则
- 可见性评估指标权重
- 情感分析词汇
- 排名关键词
- 品牌域名映射
- 引用权威性配置
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# ==================== 引用源分类规则 ====================

CITATION_TYPE_RULES = {
    "官方媒体": {
        "domains": [
            "people.com.cn", "xinhuanet.com", "cctv.com", "cnr.cn",
            "gmw.cn", "ce.cn", "china.com.cn",
        ],
        "authority": 5,
        "weight": 15,
    },
    "商业媒体": {
        "domains": [
            "thepaper.cn", "bjnews.com.cn", "caixin.com", "yicai.com",
            "jiemian.com", "21jingji.com", "ftchinese.com",
        ],
        "authority": 4,
        "weight": 12,
    },
    "科技/垂直媒体": {
        "domains": [
            "36kr.com", "ifanr.com", "ithome.com", "leiphone.com",
            "techweb.com.cn", "autohome.com.cn", "gasgoo.com",
        ],
        "authority": 4,
        "weight": 10,
    },
    "知识平台": {
        "domains": [
            "zhihu.com", "baike.baidu.com", "baidu.com", "wikipedia.org",
            "scholar.google.com",
        ],
        "authority": 3,
        "weight": 8,
    },
    "社交媒体": {
        "domains": [
            "weibo.com", "weibo.cn", "douyin.com", "tiktok.com",
            "mp.weixin.qq.com", "xiaohongshu.com",
        ],
        "authority": 2,
        "weight": 5,
    },
    "电商平台": {
        "domains": [
            "jd.com", "tmall.com", "taobao.com", "amazon.com",
            "pinduoduo.com",
        ],
        "authority": 2,
        "weight": 5,
    },
    "企业官网": {
        "domains": [],
        "authority": 3,
        "weight": 10,
        "dynamic": True,
    },
}


# ==================== 可见性分数权重 ====================

VISIBILITY_SCORE_WEIGHTS = {
    "mentioned": 40,
    "rank_1": 30,
    "rank_2_3": 20,
    "rank_4_5": 10,
    "position_prominent": 15,
    "position_early": 10,
    "position_middle": 5,
    "website_cited": 15,
    "citation_authority": 10,
    "positive_sentiment": 10,
    "neutral_sentiment": 5,
}


# ==================== 情感分析词汇 ====================

SENTIMENT_WORDS = {
    "positive": [
        "最佳", "首选", "领先", "推荐", "优秀", "出色", "值得",
        "强大", "专业", "一流", "好评", "口碑好", "性价比高",
    ],
    "negative": [
        "最差", "糟糕", "差", "避免", "问题", "缺点",
        "失望", "不足", "劣势", "风险", "争议",
    ],
}


# ==================== 排名关键词 ====================

RANK_KEYWORDS = ["首选", "第一", "top1", "排名第一"]


# ==================== 常见品牌域名映射 ====================

BRAND_DOMAIN_MAPPING = {
    # 新能源汽车
    "特斯拉": ["tesla.com", "tesla.cn"],
    "蔚来": ["nio.com", "weilai.com"],
    "小鹏": ["xpeng.com"],
    "理想": ["lixiang.com", "lixiangauto.com"],
    "比亚迪": ["byd.com", "bydauto.com.cn"],
    "极氪": ["zeekr.com"],
    "零跑": ["leapmotor.com"],
    "哪吒": ["hzauto.com", "netaauto.com"],

    # 传统汽车
    "奔驰": ["mercedes-benz.com", "mercedes-benz.com.cn"],
    "宝马": ["bmw.com", "bmw.com.cn"],
    "奥迪": ["audi.com", "audi.cn"],
    "大众": ["vw.com", "volkswagen.com.cn"],
    "丰田": ["toyota.com", "toyota.com.cn"],
    "本田": ["honda.com", "honda.com.cn"],
    "福特": ["ford.com", "ford.com.cn"],

    # 手机/消费电子
    "华为": ["huawei.com"],
    "小米": ["mi.com", "xiaomi.com"],
    "OPPO": ["oppo.com"],
    "vivo": ["vivo.com"],
    "荣耀": ["honor.cn", "hihonor.com"],
    "苹果": ["apple.com", "apple.com.cn"],
    "三星": ["samsung.com", "samsung.com.cn"],

    # 家电
    "海尔": ["haier.com"],
    "美的": ["midea.com"],
    "格力": ["gree.com"],
    "海信": ["hisense.com"],
    "创维": ["skyworth.com"],

    # 互联网/科技
    "腾讯": ["tencent.com"],
    "阿里巴巴": ["alibaba.com", "aliyun.com"],
    "百度": ["baidu.com"],
    "京东": ["jd.com"],
    "字节跳动": ["bytedance.com"],
    "网易": ["163.com", "netease.com"],

    # 金融
    "支付宝": ["alipay.com"],
    "微信支付": ["weixin.qq.com"],
    "招商银行": ["cmbchina.com"],
    "工商银行": ["icbc.com.cn"],
}


# ==================== 品牌级引用权威性配置 ====================

AUTHORITY_CONFIG_DIR = Path("./data/authority")


def get_brand_domain(brand_name: str) -> List[str]:
    """根据品牌名称获取可能的域名列表"""
    # 直接匹配
    if brand_name in BRAND_DOMAIN_MAPPING:
        return BRAND_DOMAIN_MAPPING[brand_name]

    # 尝试小写匹配
    brand_lower = brand_name.lower()
    for name, domains in BRAND_DOMAIN_MAPPING.items():
        if name.lower() == brand_lower:
            return domains

    # 未找到时返回空列表
    return []


def get_brand_authority_config(brand_name: str) -> Dict[str, Any]:
    """
    加载品牌引用权威性配置

    查找顺序：
    1. 品牌专属配置：data/authority/brands/{brand_name}.json
    2. 行业模板配置：data/authority/{industry}.json
    3. 默认配置：data/authority/default.json

    Args:
        brand_name: 品牌名称

    Returns:
        Dict: 引用权威性配置
    """
    # 品牌名转小写用于文件匹配
    brand_lower = brand_name.lower().replace(" ", "")

    # 1. 查找品牌专属配置
    brand_config_path = AUTHORITY_CONFIG_DIR / "brands" / f"{brand_lower}.json"
    if brand_config_path.exists():
        return _load_authority_config(brand_config_path)

    # 2. 使用默认配置
    default_config_path = AUTHORITY_CONFIG_DIR / "default.json"
    if default_config_path.exists():
        config = _load_authority_config(default_config_path)
        config["config_source"] = "default"
        return config

    # 3. 无配置文件时，返回硬编码的默认值
    return {
        "citation_authority_weights": {
            "官方媒体": 15,
            "商业媒体": 12,
            "科技/垂直媒体": 10,
            "知识平台": 8,
            "社交媒体": 5,
            "电商平台": 5,
            "品牌官网": 15,
        },
        "citation_domains": {
            "官方媒体": {"domains": CITATION_TYPE_RULES["官方媒体"]["domains"]},
            "商业媒体": {"domains": CITATION_TYPE_RULES["商业媒体"]["domains"]},
            "科技/垂直媒体": {"domains": CITATION_TYPE_RULES["科技/垂直媒体"]["domains"]},
            "知识平台": {"domains": CITATION_TYPE_RULES["知识平台"]["domains"]},
            "社交媒体": {"domains": CITATION_TYPE_RULES["社交媒体"]["domains"]},
            "电商平台": {"domains": CITATION_TYPE_RULES["电商平台"]["domains"]},
        },
        "custom_domains": {},
        "authority_calculation": {
            "max_count_per_type": 3,
            "score_cap": 100,
        },
        "config_source": "hardcoded",
    }


def _load_authority_config(config_path: Path) -> Dict[str, Any]:
    """加载配置文件"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        config["config_source"] = str(config_path)
        return config
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"[WARN] 配置文件加载失败: {config_path}, {e}")
        return {}


# ==================== GEO 模型路径配置 ====================

SENTIMENT_MODEL_PATH = os.getenv("SENTIMENT_MODEL_PATH", "./models/sentiment")
RECOMMENDATION_MODEL_PATH = os.getenv("RECOMMENDATION_MODEL_PATH", "./models/recommendation")
RECOMMENDATION_MAX_TOKENS = int(os.getenv("RECOMMENDATION_MAX_TOKENS", "1024"))
GEO_ANSWER_MAX_LENGTH = int(os.getenv("GEO_ANSWER_MAX_LENGTH", "20000"))


__all__ = [
    "CITATION_TYPE_RULES",
    "VISIBILITY_SCORE_WEIGHTS",
    "SENTIMENT_WORDS",
    "RANK_KEYWORDS",
    "BRAND_DOMAIN_MAPPING",
    "AUTHORITY_CONFIG_DIR",
    "get_brand_domain",
    "get_brand_authority_config",
    "SENTIMENT_MODEL_PATH",
    "RECOMMENDATION_MODEL_PATH",
    "RECOMMENDATION_MAX_TOKENS",
    "GEO_ANSWER_MAX_LENGTH",
]