"""
通义千问 (Qwen) API客户端

阿里云DashScope API文档: https://help.aliyun.com/document_detail/2712195.html
"""

import os
from typing import List, Optional
from platforms.base import BaseAIClient, AIResponse, AIClientFactory, PLATFORMS
from config.settings import settings


class QwenClient(BaseAIClient):
    """通义千问API客户端"""

    def __init__(self, api_key: str = None, model: str = None):
        # 从配置读取
        platform_config = PLATFORMS.get("qwen", {})
        api_key = api_key or os.environ.get(platform_config.get("api_key_env", "QWEN_API_KEY"))
        if not api_key:
            # 从 settings.geo_tracking 获取
            api_key = settings.geo_tracking.qwen_api_key
        if not api_key:
            raise ValueError("缺少QWEN_API_KEY，请设置环境变量")

        model = model or platform_config.get("default_model", "qwen-plus")
        api_base = platform_config.get("api_base", "https://dashscope.aliyuncs.com/compatible-mode/v1")

        # 从配置读取 enable_search
        self.enable_search = platform_config.get("enable_search", False)
        
        super().__init__(
            api_key=api_key,
            api_base=api_base,
            model=model
        )

    def query(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        enable_search: bool = None,  # 启用联网搜索增强（None时使用配置值）
        use_cache=None,
    ) -> AIResponse:
        """调用通义千问API"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # OpenAI兼容格式
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            response = self._make_request(
                f"{self.api_base}/chat/completions",
                headers=headers,
                data=data,
            )

            if response.status_code != 200:
                return AIResponse(
                    platform="qwen",
                    platform_name="通义千问",
                    prompt=prompt,
                    content="",
                    citations=[],
                    success=False,
                    error=f"API错误 {response.status_code}: {response.text[:200]}",
                    latency=0,
                    cached=False,
                    raw_response=None,
                )

            result = response.json()

            # OpenAI兼容格式解析
            choices = result.get("choices", [{}])
            content = choices[0].get("message", {}).get("content", "")

            # 提取搜索引用
            citations = []
            search_info = result.get("search_info", [])
            if search_info:
                for item in search_info:
                    if isinstance(item, dict) and "url" in item:
                        if self._is_valid_citation(item["url"]):
                            citations.append(item["url"])

            # 也从文本中提取
            citations.extend(self._extract_urls_from_text(content))
            citations = list(set(citations))

            return AIResponse(
                platform="qwen",
                platform_name="通义千问",
                prompt=prompt,
                content=content,
                citations=citations,
                success=True,
                error=None,
                latency=0,
                cached=False,
                raw_response=result,
            )

        except Exception as e:
            return AIResponse(
                platform="qwen",
                platform_name="通义千问",
                prompt=prompt,
                content="",
                citations=[],
                success=False,
                error=str(e),
                latency=0,
                cached=False,
                raw_response=None,
            )


# 注册到工厂
AIClientFactory.register("qwen", QwenClient)