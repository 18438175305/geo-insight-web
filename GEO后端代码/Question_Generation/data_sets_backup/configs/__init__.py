"""
数据集配置模块

品牌配置、领域配置
"""

from pathlib import Path
import json

CONFIG_DIR = Path(__file__).parent


def load_brand_configs() -> dict:
    """加载完整品牌配置"""
    config_path = CONFIG_DIR / "brand_configs.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_simple_brand_configs() -> dict:
    """加载简化品牌配置"""
    config_path = CONFIG_DIR / "brand_configs_simple.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)