"""
AI平台API客户端基础类

职责：
1. 定义统一的API调用接口
2. 处理请求错误和重试逻辑
3. 标准化返回结果格式

注意：这不是爬虫，而是调用公域AI平台的官方API。
"""

import os
import time
import hashlib
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import urlparse
import requests

# 统一使用 core.state 中的 AIResponse 定义
from core.state import AIResponse


class BaseAIClient(ABC):
    """AI平台API客户端基类"""

    DEFAULT_TIMEOUT = 60
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def __init__(self, api_key: str, api_base: str, model: str):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.session = requests.Session()

    @abstractmethod
    def query(self, prompt: str, **kwargs) -> AIResponse:
        """
        向AI平台发送提问并获取响应

        Args:
            prompt: 用户提问内容
            **kwargs: 平台特定参数

        Returns:
            AIResponse: 标准化的响应结果
        """
        pass

    def _make_request(
        self,
        url: str,
        headers: Dict[str, str],
        data: Dict[str, Any],
        timeout: int = None,
    ) -> requests.Response:
        """发送HTTP请求（带重试机制）"""
        timeout = timeout or self.DEFAULT_TIMEOUT

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=timeout,
                )
                return response
            except requests.exceptions.Timeout:
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue
                raise TimeoutError(f"请求超时，重试{self.MAX_RETRIES}次后失败")
            except requests.exceptions.RequestException as e:
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                    continue
                raise ConnectionError(f"请求失败: {str(e)}")

    def _extract_urls_from_text(self, text: str) -> List[str]:
        """从回复文本中提取URL引用"""
        pattern = r'https?://[^\s)\]"\'一-鿿]+'
        urls = re.findall(pattern, text)

        cleaned = []
        for url in urls:
            url = re.sub(r'[),.;:!?]+$', '', url)
            if self._is_valid_citation(url):
                cleaned.append(url)
        return cleaned

    def _is_valid_citation(self, url: str) -> bool:
        """判断URL是否为有效的引用来源（过滤AI平台自身域名）"""
        blocked_hosts = [
            "doubao.com", "bytedance.com",
            "deepseek.com",
            "hunyuan.tencent.com", "tencent.com",
            "dashscope.aliyuncs.com", "aliyun.com", "alibaba.com",
            "moonshot.cn", "kimi.ai",
            # CDN和追踪域名
            "cloudfront.net", "cdn.jsdelivr.net", "cdnjs.cloudflare.com",
            "google-analytics.com", "googletagmanager.com",
        ]

        try:
            parsed = urlparse(url)
            host = parsed.hostname.lower() if parsed.hostname else ""

            for blocked in blocked_hosts:
                if host == blocked or host.endswith(f".{blocked}"):
                    return False

            # 过滤静态资源
            asset_extensions = ['.js', '.css', '.png', '.jpg', '.gif', '.svg', '.ico', '.woff']
            if any(parsed.path.lower().endswith(ext) for ext in asset_extensions):
                return False

            return True
        except Exception:
            return False

    def _get_cache_key(self, prompt: str) -> str:
        """生成缓存键"""
        return hashlib.md5(f"{self.model}:{prompt}".encode()).hexdigest()


class AIClientFactory:
    """AI平台客户端工厂"""

    _clients: Dict[str, type] = {}           # 注册的客户端类
    _instances: Dict[str, BaseAIClient] = {} # 缓存的客户端实例

    @classmethod
    def register(cls, platform: str, client_class: type):
        """注册平台客户端"""
        cls._clients[platform] = client_class

    @classmethod
    def create(cls, platform: str, **kwargs) -> BaseAIClient:
        """
        创建或获取平台客户端实例

        每个平台只初始化一次，后续调用返回缓存的实例
        """
        # 如果已有缓存的实例，直接返回
        if platform in cls._instances:
            return cls._instances[platform]

        # 否则创建新实例并缓存
        if platform not in cls._clients:
            return None
        client_class = cls._clients[platform]
        instance = client_class(**kwargs)
        cls._instances[platform] = instance
        return instance

    @classmethod
    def get_supported_platforms(cls) -> List[str]:
        """获取支持的平台列表"""
        return list(cls._clients.keys())

    @classmethod
    def clear_instances(cls):
        """清空缓存的客户端实例（用于重新初始化或切换API密钥）"""
        cls._instances.clear()

    @classmethod
    def get_cached_platforms(cls) -> List[str]:
        """获取已缓存的平台列表"""
        return list(cls._instances.keys())


class InMemoryCache:
    """内存缓存（避免重复请求相同提问）"""

    def __init__(self, ttl_seconds: int = 3600):
        self._cache: Dict[str, Dict] = {}
        self._ttl = ttl_seconds

    def get(self, key: str) -> Optional[AIResponse]:
        """获取缓存"""
        entry = self._cache.get(key)
        if entry and entry["expires_at"] > time.time():
            result = entry["value"]
            result["cached"] = True
            return result
        return None

    def set(self, key: str, value: AIResponse):
        """设置缓存"""
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + self._ttl,
        }

    def clear(self):
        """清空缓存"""
        self._cache.clear()


# 平台配置
PLATFORMS = {
    "deepseek": {
        "name": "DeepSeek",
        "api_key_env": "DEEPSEEK_API_KEY",
        "api_base": "https://api.deepseek.com",
        "default_model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    },
    "qwen": {
        "name": "通义千问",
        "api_key_env": "QWEN_API_KEY",
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": os.getenv("QWEN_MODEL", "qwen-plus"),
        "enable_search": os.getenv("QWEN_ENABLE_SEARCH", "true").lower() == "true",
    },
    "kimi": {
        "name": "Kimi",
        "api_key_env": "KIMI_API_KEY",
        "api_base": "https://api.moonshot.cn/v1",
        "default_model": os.getenv("KIMI_MODEL", "moonshot-v1-8k"),
    },
    "doubao": {
        "name": "豆包",
        "api_key_env": "DOUBAO_API_KEY",
        "endpoint_env": "DOUBAO_ENDPOINT_ID",
        "api_base": "https://ark.cn-beijing.volces.com/api/v3",
        "default_model": os.getenv("DOUBAO_MODEL", "doubao-pro-32k"),
    },
    "yuanbao": {
        "name": "元宝",
        "api_key_env": "YUANBAO_API_KEY",
        "secret_key_env": "YUANBAO_SECRET_KEY",
        "api_base": "https://hunyuan.tencentcloudapi.com",
        "default_model": os.getenv("YUANBAO_MODEL", "hunyuan-lite"),
    },
}


__all__ = [
    "AIResponse",
    "BaseAIClient",
    "AIClientFactory",
    "InMemoryCache",
    "PLATFORMS",
]