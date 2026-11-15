"""
爬虫调度管理器

协调多个爬虫，统一管理爬取任务
"""

from typing import List, Dict
from .base_crawler import CrawledDocument
from .official_site_crawler import OfficialSiteCrawler
from .zhihu_crawler import ZhihuCrawler
from .xiaohongshu_crawler import XiaohongshuCrawler
from .whitepaper_crawler import WhitepaperCrawler
import json
from pathlib import Path
from config.settings import settings


class CrawlerManager:
    """
    爬虫调度管理器

    协调多个爬虫，统一管理爬取任务
    """

    def __init__(self, brand_name: str):
        self.brand_name = brand_name
        self.crawlers = {
            "official_site": OfficialSiteCrawler(brand_name),
            "zhihu": ZhihuCrawler(brand_name),
            "xiaohongshu": XiaohongshuCrawler(brand_name),
            "whitepaper": WhitepaperCrawler(brand_name),
        }

    def run_all_crawlers(self, configs: Dict[str, Dict]) -> List[CrawledDocument]:
        """运行所有启用的爬虫 : Args: configs: 各爬虫配置字典; Returns:所有爬取文档的合并列表"""
        all_documents = []
        for source_type, config in configs.items():
            if source_type in self.crawlers and config.get("enabled", True):
                crawler = self.crawlers[source_type]
                try:
                    documents = crawler.crawl(config)
                    all_documents.extend(documents)
                    print(f"[INFO] {source_type}: crawled {len(documents)} documents")
                except Exception as e:
                    print(f"[ERROR] {source_type} crawler failed: {str(e)}")
        return all_documents

    def run_single_crawler(
        self,
        source_type: str,
        config: Dict
    ) -> List[CrawledDocument]:
        """
        运行单个爬虫

        Args:
            source_type: 来源类型
            config: 爬取配置

        Returns:
            爬取文档列表
        """
        if source_type not in self.crawlers:
            raise ValueError(f"Unknown source type: {source_type}")

        return self.crawlers[source_type].crawl(config)

    def save_documents(
        self,
        documents: List[CrawledDocument],
        output_path: str
    ):
        """
        保存爬取文档

        Args:
            documents: 文档列表
            output_path: 输出路径
        """
        output_data = {
            "brand_name": self.brand_name,
            "total_documents": len(documents),
            "crawl_timestamp": documents[0].get('crawl_timestamp', 0) if documents else 0,
            "documents": documents,
            "source_summary": self._get_source_summary(documents),
        }

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"[INFO] Saved {len(documents)} documents to {output_path}")

    def load_documents(self, input_path: str) -> List[CrawledDocument]:
        """
        加载已保存的爬取文档

        Args:
            input_path: 输入路径

        Returns:
            文档列表
        """
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("documents", [])

    def _get_source_summary(self, documents: List[CrawledDocument]) -> Dict:
        """
        获取来源统计摘要

        Args:
            documents: 文档列表

        Returns:
            统计摘要
        """
        summary = {}
        for doc in documents:
            source_type = doc.get("source_type", "unknown")
            summary[source_type] = summary.get(source_type, 0) + 1
        return summary

    def get_default_configs(self) -> Dict[str, Dict]:
        """
        获取默认爬虫配置

        Returns:
            默认配置字典
        """
        return {
            "official_site": {
                "enabled": True,
                "base_url": f"https://www.{self.brand_name.lower().replace(' ', '')}.com",
                "target_pages": [
                    {"path": "/", "category": "品牌介绍"},
                    {"path": "/products", "category": "产品介绍"},
                    {"path": "/about", "category": "品牌历史"},
                ],
                "max_pages": 10,
            },
            "zhihu": {
                "enabled": True,
                "search_keywords": [self.brand_name],
                "max_items": 15,
            },
            "xiaohongshu": {
                "enabled": False,
                "search_keywords": [self.brand_name],
                "max_notes": 20,
            },
            "whitepaper": {
                "enabled": True,
                "pdf_files": [],
            },
        }

    def get_available_source_types(self) -> List[str]:
        """
        获取可用的来源类型列表

        Returns:
            来源类型列表
        """
        return list(self.crawlers.keys())


def crawl_brand_data(
    brand_name: str,
    configs: Dict = None,
    output_path: str = None,
) -> List[CrawledDocument]:
    """
    爬取品牌数据的便捷函数

    Args:
        brand_name: 品牌名称
        configs: 爬取配置（可选，使用默认配置）
        output_path: 输出路径（可选）

    Returns:
        爬取文档列表
    """
    manager = CrawlerManager(brand_name)

    if configs is None:
        configs = manager.get_default_configs()

    documents = manager.run_all_crawlers(configs)

    if output_path:
        manager.save_documents(documents, output_path)

    return documents