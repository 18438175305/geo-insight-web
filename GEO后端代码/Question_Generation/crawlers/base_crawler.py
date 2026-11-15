"""
爬虫基类
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, TypedDict, Any
from datetime import datetime
import hashlib
import re
import random
import time
import requests
from config.settings import settings


class CrawledDocument(TypedDict):
    """爬取文档结构"""
    doc_id: str
    title: str
    content: str
    source_type: str
    source_url: str
    source_date: Optional[int]
    crawl_timestamp: int
    keywords: List[str]
    category: str
    brand_name: str
    quality_score: float


class BaseCrawler(ABC):
    """爬虫基类"""

    def __init__(self, brand_name: str):
        self.brand_name = brand_name
        self.crawl_timestamp = int(datetime.now().timestamp() * 1000)
        self.timeout = settings.crawler.timeout
        self.retry_count = settings.crawler.retry_count
        self.session = requests.Session()

    @abstractmethod
    def crawl(self, config: Dict) -> List[CrawledDocument]:
        pass

    @abstractmethod
    def get_source_type(self) -> str:
        pass

    def generate_doc_id(self, content: str, url: str) -> str:
        hash_input = f"{url}_{content[:100]}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        return f"{self.get_source_type()}_{hash_value}"

    def calculate_quality_score(self, content: str) -> float:
        if not content:
            return 0.0
        length_score = min(len(content) / 1000, 1.0) * 0.3
        keyword_count = len(self.extract_keywords(content))
        density_score = min(keyword_count / 10, 1.0) * 0.3
        format_score = 0.4 if self._check_format_integrity(content) else 0.2
        return round(length_score + density_score + format_score, 2)

    def _check_format_integrity(self, content: str) -> bool:
        return len(content) > 100 and content.strip() != ""

    def extract_keywords(self, content: str) -> List[str]:
        keywords = [self.brand_name]
        words = re.findall(r'[一-龥]{2,4}', content)
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        keywords.extend([w[0] for w in top_words])
        return keywords

    def delay(self):
        delay_min, delay_max = settings.crawler.delay_range
        delay_time = random.uniform(delay_min, delay_max)
        time.sleep(delay_time)

    def get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": settings.crawler.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    def safe_get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        带重试的 GET 请求，自动修正编码
        """
        for attempt in range(self.retry_count):
            try:
                self.delay()
                response = self.session.get(url, **kwargs)
                # 自动检测并修正编码
                if response.encoding and response.encoding.lower() in ('iso-8859-1', 'latin-1'):
                    # 检测实际编码
                    detected = response.apparent_encoding
                    if detected and detected.lower() != response.encoding.lower():
                        response.encoding = detected
                return response
            except Exception as e:
                print(f"[WARN] Request failed (attempt {attempt + 1}): {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(2 ** attempt)
        return None
