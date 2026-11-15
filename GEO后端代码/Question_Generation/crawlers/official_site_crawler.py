"""
官方网站爬虫

爬取品牌官方网站的产品介绍、使用说明等页面
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from .base_crawler import BaseCrawler, CrawledDocument
import re
from urllib.parse import urljoin, urlparse


class OfficialSiteCrawler(BaseCrawler):
    """
    官网爬虫

    爬取品牌官方网站的产品介绍、使用说明等页面
    """

    def get_source_type(self) -> str:
        return "official_site"

    def crawl(self, config: Dict) -> List[CrawledDocument]:
        """
        爬取官网内容

        Config格式:
        {
            "enabled": true,
            "base_url": "https://www.yunnanbaiyao.com.cn",
            "target_pages": [
                {"path": "/", "category": "品牌介绍"},
                {"path": "/list/*", "category": "产品介绍", "max_items": 10},
                {"path": "/about", "category": "品牌历史"},
            ],
            "max_pages": 20,
        }

        Args:
            config: 爬取配置

        Returns:
            爬取文档列表
        """
        documents = []
        base_url = config.get("base_url", "")
        target_pages = config.get("target_pages", [])
        max_pages = config.get("max_pages", 20)

        if not base_url:
            print(f"[WARN] No base_url provided for {self.brand_name}")
            return documents

        for page_config in target_pages[:max_pages]:
            path = page_config.get("path", "")

            if "*" in path:
                # 通配符模式：自动发现链接
                discovered_docs = self._crawl_with_wildcard(base_url, path, page_config)
                documents.extend(discovered_docs)
            else:
                # 直接爬取单页
                url = f"{base_url}{path}"
                try:
                    doc = self._crawl_page(url, page_config)
                    if doc:
                        documents.append(doc)
                        print(f"[INFO] Crawled: {url}")
                except Exception as e:
                    print(f"[ERROR] Failed to crawl {url}: {str(e)}")

        return documents

    def _crawl_with_wildcard(self, base_url: str, path_pattern: str, page_config: Dict) -> List[CrawledDocument]:
        """
        使用通配符发现并爬取匹配的链接

        Args:
            base_url: 基础URL
            path_pattern: 包含*的路径模式，如 "/list/*"
            page_config: 页面配置

        Returns:
            爬取文档列表
        """
        documents = []
        max_items = page_config.get("max_items", 10)
        category = page_config.get("category", "官网内容")

        # 构造发现URL（去掉通配符部分）
        pattern_parts = path_pattern.split("*")
        discovery_path = pattern_parts[0].rstrip("/")
        discovery_url = f"{base_url}{discovery_path}" if discovery_path else base_url

        print(f"[INFO] Discovering links from {discovery_url} with pattern {path_pattern}")

        # 获取页面并提取链接
        try:
            response = self.safe_get(
                discovery_url,
                headers=self.get_headers(),
                timeout=self.timeout,
            )
            if response is None or response.status_code != 200:
                return documents

            soup = BeautifulSoup(response.text, 'html.parser')

            # 构造匹配正则
            pattern_regex = self._build_pattern_regex(base_url, path_pattern)

            # 提取所有匹配的链接
            matched_urls = set()
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                full_url = urljoin(base_url, href)
                if pattern_regex.match(full_url):
                    matched_urls.add(full_url)

            print(f"[INFO] Found {len(matched_urls)} matching links")

            # 爬取匹配的链接
            for url in list(matched_urls)[:max_items]:
                try:
                    doc = self._crawl_page(url, {"category": category})
                    if doc:
                        documents.append(doc)
                        print(f"[INFO] Crawled: {url}")
                except Exception as e:
                    print(f"[ERROR] Failed to crawl {url}: {str(e)}")

        except Exception as e:
            print(f"[ERROR] Failed to discover links: {str(e)}")

        return documents

    def _build_pattern_regex(self, base_url: str, path_pattern: str) -> re.Pattern:
        """
        构造通配符匹配正则

        Args:
            base_url: 基础URL
            path_pattern: 路径模式，如 "/list/*"

        Returns:
            正则表达式
        """
        # 将 path_pattern 转换为正则
        # "/list/*" -> "^https://www\.xxx\.com/list/.*$"
        pattern = path_pattern.replace("*", ".*")
        pattern = pattern.replace("/", r"/")
        full_pattern = f"^{re.escape(base_url)}{pattern}$"
        return re.compile(full_pattern)

    def _crawl_page(self, url: str, page_config: Dict) -> Optional[CrawledDocument]:
        """
        爬取单个页面

        Args:
            url: 页面URL
            page_config: 页面配置

        Returns:
            爬取文档或None
        """
        response = self.safe_get(
            url,
            headers=self.get_headers(),
            timeout=self.timeout,
        )

        if response is None or response.status_code != 200:
            return None

        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取标题
        title = self._extract_title(soup)

        # 提取主要内容
        content = self._extract_content(soup)

        # 提取发布日期
        source_date = self._extract_date(soup)

        if not content or len(content) < 50:
            return None

        doc_id = self.generate_doc_id(content, url)

        return CrawledDocument(
            doc_id=doc_id,
            title=title,
            content=content,
            source_type=self.get_source_type(),
            source_url=url,
            source_date=source_date,
            crawl_timestamp=self.crawl_timestamp,
            keywords=self.extract_keywords(content),
            category=page_config.get("category", "官网内容"),
            brand_name=self.brand_name,
            quality_score=self.calculate_quality_score(content),
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """
        提取页面标题

        Args:
            soup: BeautifulSoup对象

        Returns:
            标题
        """
        # 尝试多种标题提取方式
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            # 清理网站名称后缀
            title = re.sub(rf'[-_|]\s*{self.brand_name}.*$', '', title)
            return title

        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()

        # 查找meta title
        meta_title = soup.find('meta', property='og:title')
        if meta_title:
            return meta_title.get('content', '').strip()

        return ""

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """
        提取主要内容

        Args:
            soup: BeautifulSoup对象

        Returns:
            内容文本
        """
        # 移除导航、脚本、样式等无关元素
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()

        # 尝试找到主要内容区域
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('div', class_='content') or
            soup.find('div', class_='main') or
            soup.find('div', id='content') or
            soup.find('body')
        )

        if main_content:
            content = main_content.get_text(separator='\n', strip=True)
        else:
            content = soup.get_text(separator='\n', strip=True)

        # 清理内容
        content = self._clean_content(content)

        return content

    def _clean_content(self, content: str) -> str:
        """
        清理内容

        Args:
            content: 原始内容

        Returns:
            清理后的内容
        """
        # 移除多余空白
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)

        # 移除常见的无关文本
        content = re.sub(r'版权所有.*$', '', content)
        content = re.sub(r'Copyright.*$', '', content)
        content = re.sub(r'联系方式.*$', '', content)

        return content.strip()

    def _extract_date(self, soup: BeautifulSoup) -> Optional[int]:
        """
        提取发布日期

        Args:
            soup: BeautifulSoup对象

        Returns:
            时间戳或None
        """
        # 查找时间标签
        time_tag = soup.find('time')
        if time_tag and time_tag.get('datetime'):
            try:
                # 解析ISO格式日期
                from datetime import datetime
                date_str = time_tag.get('datetime')
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return int(dt.timestamp())
            except Exception:
                pass

        # 查找meta date
        meta_date = soup.find('meta', property='article:published_time')
        if meta_date:
            try:
                from datetime import datetime
                date_str = meta_date.get('content')
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return int(dt.timestamp())
            except Exception:
                pass

        return None