"""
知乎爬虫

爬取知乎问答、文章等内容
"""

import requests
from typing import List, Dict, Optional
from .base_crawler import BaseCrawler, CrawledDocument
import json
import re
import hashlib
from pathlib import Path


class ZhihuCrawler(BaseCrawler):
    """
    知乎爬虫

    爬取知乎问答、文章等内容
    """

    def get_source_type(self) -> str:
        return "zhihu"

    def load_cookie(self) -> str:
        """从配置文件加载知乎Cookie"""
        cookie_file = Path(__file__).parent.parent / "data" / "crawl_configs" / "cookies.json"
        if cookie_file.exists():
            with open(cookie_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("zhihu", {}).get("cookie", "")
        return ""

    def get_headers(self) -> Dict[str, str]:
        """获取知乎专用请求头"""
        headers = super().get_headers()
        headers.update({
            "x-api-version": "3.0.40",
            "x-zse-83": "3_2.0",
        })
        # 加载Cookie
        cookie = self.load_cookie()
        if cookie:
            headers["Cookie"] = cookie
        return headers

    def crawl(self, config: Dict) -> List[CrawledDocument]:
        """
        爬取知乎内容

        Config格式示例:
        {
            "enabled": true,
            "search_keywords": ["品牌名", "品牌功效"],
            "max_items": 20,
        }

        Args:
            config: 爬取配置

        Returns:
            爬取文档列表
        """
        documents = []
        keywords = config.get("search_keywords", [self.brand_name])
        max_items = config.get("max_items", 20)
        items_per_keyword = max(1, max_items // len(keywords))

        for keyword in keywords:
            questions = self._search_questions(keyword, limit=items_per_keyword)
            for q in questions:
                try:
                    doc = self._crawl_question(q)
                    if doc:
                        documents.append(doc)
                        print(f"[INFO] Crawled Zhihu Q: {q.get('title', '')}")
                except Exception as e:
                    print(f"[ERROR] Failed to crawl Zhihu question: {str(e)}")

        return documents

    def _search_questions(self, keyword: str, limit: int = 20) -> List[Dict]:
        """
        搜索相关问题

        Args:
            keyword: 搜索关键词
            limit: 返回数量

        Returns:
            问题列表
        """
        # 使用知乎搜索API（注意：知乎API可能有变化）
        url = "https://www.zhihu.com/api/v4/search_v3"
        params = {
            "t": "general",
            "q": keyword,
            "correction": 1,
            "limit": limit,
            "sort": "relevance",
        }

        response = self.safe_get(url,
            params=params,
            headers=self.get_headers(),
            timeout=self.timeout,
        )

        if response is None:
            # 降级：使用模拟数据
            return self._get_mock_questions(keyword)

        try:
            data = response.json()
            return data.get("data", [])
        except Exception:
            return self._get_mock_questions(keyword)

    def _get_mock_questions(self, keyword: str) -> List[Dict]:
        """
        获取模拟问题数据（当API不可用时）

        Args:
            keyword: 关键词

        Returns:
            模拟问题列表
        """
        # 基于关键词生成模拟问题
        mock_questions = [
            {
                "id": f"mock_{hashlib.md5(keyword.encode()).hexdigest()[:8]}",
                "type": "question",
                "title": f"{keyword}怎么样？",
                "url": f"https://www.zhihu.com/question/mock_1",
            },
            {
                "id": f"mock_{hashlib.md5((keyword+'使用').encode()).hexdigest()[:8]}",
                "type": "question",
                "title": f"{keyword}怎么使用？",
                "url": f"https://www.zhihu.com/question/mock_2",
            },
            {
                "id": f"mock_{hashlib.md5((keyword+'功效').encode()).hexdigest()[:8]}",
                "type": "question",
                "title": f"{keyword}有什么功效？",
                "url": f"https://www.zhihu.com/question/mock_3",
            },
        ]
        return mock_questions

    def _crawl_question(self, question_data: Dict) -> Optional[CrawledDocument]:
        """
        爬取单个问答

        Args:
            question_data: 问题数据

        Returns:
            爬取文档或None
        """
        question_id = question_data.get("id", "unknown")
        question_title = question_data.get("title", "")
        question_url = question_data.get("url", f"https://www.zhihu.com/question/{question_id}")

        # 获取高赞回答
        answers = self._get_top_answers(question_id)

        # 组合内容：问题 + 高赞回答
        content_parts = [f"问题：{question_title}"]
        for answer in answers[:3]:
            excerpt = answer.get('excerpt', '') or answer.get('content', '')
            if excerpt:
                content_parts.append(f"\n回答：{excerpt[:500]}")

        content = "\n".join(content_parts)

        if len(content) < 50:
            return None

        doc_id = self.generate_doc_id(content, question_url)

        return CrawledDocument(
            doc_id=doc_id,
            title=question_title,
            content=content,
            source_type=self.get_source_type(),
            source_url=question_url,
            source_date=None,
            crawl_timestamp=self.crawl_timestamp,
            keywords=self.extract_keywords(content),
            category="知乎问答",
            brand_name=self.brand_name,
            quality_score=self.calculate_quality_score(content),
        )

    def _get_top_answers(self, question_id: str) -> List[Dict]:
        """
        获取问题的高赞回答

        Args:
            question_id: 问题ID

        Returns:
            回答列表
        """
        url = f"https://www.zhihu.com/api/v4/questions/{question_id}/answers"
        params = {
            "limit": 10,
            "sort_by": "default",  # 按默认排序（通常包含高赞）
        }

        response = self.safe_get(url,
            params=params,
            headers=self.get_headers(),
            timeout=self.timeout,
        )

        if response is None:
            return []

        try:
            data = response.json()
            return data.get("data", [])
        except Exception:
            return []

    def extract_keywords(self, content: str) -> List[str]:
        """提取知乎关键词"""
        keywords = [self.brand_name, "知乎"]

        if "怎么" in content or "如何" in content:
            keywords.append("使用方法")
        if "功效" in content or "效果" in content:
            keywords.append("功效说明")
        if "多少钱" in content or "价格" in content:
            keywords.append("价格信息")

        return keywords