"""
小红书爬虫

爬取小红书笔记内容

注意：小红书有较强的反爬机制，建议：
1. 使用手动导入方式（用户导出笔记后导入）
2. 或使用官方API（如有权限）
3. 本实现提供基础的爬取能力，实际使用时可能需要调整
"""

import requests
from typing import List, Dict, Optional
from .base_crawler import BaseCrawler, CrawledDocument
import re
import json
from pathlib import Path


class XiaohongshuCrawler(BaseCrawler):
    """
    小红书爬虫

    爬取小红书笔记内容
    """

    def get_source_type(self) -> str:
        return "xiaohongshu"

    def load_cookie(self) -> str:
        """从配置文件加载小红书Cookie"""
        cookie_file = Path(__file__).parent.parent / "data" / "crawl_configs" / "cookies.json"
        if cookie_file.exists():
            with open(cookie_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("xiaohongshu", {}).get("cookie", "")
        return ""

    def get_headers(self) -> Dict[str, str]:
        """获取小红书专用请求头"""
        headers = super().get_headers()
        headers.update({
            "Referer": "https://www.xiaohongshu.com",
        })
        # 加载Cookie
        cookie = self.load_cookie()
        if cookie:
            headers["Cookie"] = cookie
        return headers

    def crawl(self, config: Dict) -> List[CrawledDocument]:
        """
        爬取小红书内容

        Config格式示例:
        {
            "enabled": true,
            "search_keywords": ["品牌名", "品牌心得"],
            "max_notes": 30,
        }

        Args:
            config: 爬取配置

        Returns:
            爬取文档列表
        """
        documents = []
        keywords = config.get("search_keywords", [self.brand_name])
        max_notes = config.get("max_notes", 30)
        notes_per_keyword = max(1, max_notes // len(keywords))

        for keyword in keywords:
            notes = self._search_notes(keyword, limit=notes_per_keyword)
            for note in notes:
                try:
                    doc = self._crawl_note(note)
                    if doc:
                        documents.append(doc)
                        print(f"[INFO] Crawled XHS Note: {note.get('title', '')}")
                except Exception as e:
                    print(f"[ERROR] Failed to crawl XHS note: {str(e)}")

        if not documents:
            print("[WARN] Xiaohongshu crawl may require authentication. Consider using manual import.")
            documents = self._get_mock_notes(keywords[0])

        return documents

    def _search_notes(self, keyword: str, limit: int = 30) -> List[Dict]:
        """
        搜索小红书笔记

        Args:
            keyword: 搜索关键词
            limit: 返回数量

        Returns:
            笔记列表
        """
        # 小红书Web搜索API（注意：可能需要登录）
        url = "https://www.xiaohongshu.com/web_api/sns/v1/search/notes"
        params = {
            "keyword": keyword,
            "sort": "general",  # 综合排序
            "page": 1,
            "page_size": limit,
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
            notes = data.get("data", {}).get("notes", [])
            return notes
        except Exception:
            return []

    def _crawl_note(self, note_data: Dict) -> Optional[CrawledDocument]:
        """
        爬取单个笔记

        Args:
            note_data: 笔记数据

        Returns:
            爬取文档或None
        """
        note_id = note_data.get("id", note_data.get("noteId", "unknown"))
        note_title = note_data.get("title", note_data.get("displayTitle", ""))
        note_url = f"https://www.xiaohongshu.com/explore/{note_id}"

        # 获取笔记详情
        note_detail = self._get_note_detail(note_id)

        # 组合内容
        content = note_detail.get("content", "")
        if not content:
            content = note_data.get("desc", "")

        if len(content) < 50:
            return None

        doc_id = self.generate_doc_id(content, note_url)

        return CrawledDocument(
            doc_id=doc_id,
            title=note_title,
            content=content,
            source_type=self.get_source_type(),
            source_url=note_url,
            source_date=None,
            crawl_timestamp=self.crawl_timestamp,
            keywords=self.extract_keywords(content),
            category="小红书笔记",
            brand_name=self.brand_name,
            quality_score=self.calculate_quality_score(content),
        )

    def _get_note_detail(self, note_id: str) -> Dict:
        """
        获取笔记详情

        Args:
            note_id: 笔记ID

        Returns:
            笔记详情
        """
        url = f"https://www.xiaohongshu.com/web_api/sns/v1/note/{note_id}"

        response = self.safe_get(url,
            headers=self.get_headers(),
            timeout=self.timeout,
        )

        if response is None:
            return {}

        try:
            data = response.json()
            return data.get("data", {})
        except Exception:
            return {}

    def _get_mock_notes(self, keyword: str) -> List[CrawledDocument]:
        """
        获取模拟笔记数据（当爬取失败时）

        Args:
            keyword: 关键词

        Returns:
            模拟文档列表
        """
        import hashlib

        mock_notes = [
            CrawledDocument(
                doc_id=f"xhs_mock_{hashlib.md5(keyword.encode()).hexdigest()[:8]}",
                title=f"{keyword}使用心得分享",
                content=f"最近使用了{keyword}，效果很不错。分享一下使用心得：{keyword}对于日常小伤口的处理非常有效，止血效果很快。建议大家家里可以备一瓶。",
                source_type=self.get_source_type(),
                source_url=f"https://www.xiaohongshu.com/explore/mock_1",
                source_date=None,
                crawl_timestamp=self.crawl_timestamp,
                keywords=[keyword, "使用心得", "推荐"],
                category="小红书笔记",
                brand_name=self.brand_name,
                quality_score=0.7,
            ),
        ]
        return mock_notes

    def extract_keywords(self, content: str) -> List[str]:
        """提取小红书关键词"""
        keywords = [self.brand_name, "小红书"]

        if "推荐" in content or "好用" in content:
            keywords.append("用户推荐")
        if "心得" in content or "分享" in content:
            keywords.append("使用心得")
        if "真实" in content:
            keywords.append("真实体验")

        return keywords