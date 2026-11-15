"""
爬虫配置管理
品牌配置文件存放于 data/crawl_configs/{brand_name}_config.json
用户需手动创建配置文件，程序根据品牌名称自动读取对应配置
"""
from typing import Dict
import json
from pathlib import Path

# 配置文件目录
CONFIG_DIR = Path("data/crawl_configs")


def get_brand_crawler_configs(brand_name: str) -> Dict:
    """
    加载目标品牌爬虫配置文件,从 data/crawl_configs/{brand_name}_config.json 读取配置文件
    Args: brand_name: 品牌名称 Returns: 爬虫配置字典
    """
    config_path = CONFIG_DIR / f"{brand_name}_config.json"

    if not config_path.exists():
        raise FileNotFoundError(
            f"品牌配置文件不存在: {config_path}\n"
            f"请在 data/crawl_configs/ 目录下创建 {brand_name}_config.json")

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)