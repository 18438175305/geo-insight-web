"""
Kimi API客户端

Moonshot API文档: https://platform.moonshot.cn/docs
API格式: OpenAI兼容
"""

import os
from typing import List, Optional
from platforms.base import BaseAIClient, AIResponse, AIClientFactory, PLATFORMS
from config.settings import settings


class KimiClient(BaseAIClient):
    """Kimi API客户端"""

    def __init__(self, api_key: str = None, model: str = None):
        # 从配置读取
        platform_config = PLATFORMS.get("kimi", {})
        api_key = api_key or os.environ.get(platform_config.get("api_key_env", "KIMI_API_KEY"))
        if not api_key:
            # 从 settings.geo_tracking 获取
            api_key = settings.geo_tracking.kimi_api_key
        if not api_key:
            raise ValueError("缺少KIMI_API_KEY，请设置环境变量")

        model = model or platform_config.get("default_model", "moonshot-v1-8k")
        api_base = platform_config.get("api_base", "https://api.moonshot.cn/v1")

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
        use_cache=None,
    ) -> AIResponse:
        """调用Kimi API获取回复"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        try:
            response = self._make_request(
                f"{self.api_base}/chat/completions",
                headers=headers,
                data=data,
            )

            if response.status_code != 200:
                return AIResponse(
                    platform="kimi",
                    platform_name="Kimi",
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
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            citations = self._extract_urls_from_text(content)

            return AIResponse(
                platform="kimi",
                platform_name="Kimi",
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
                platform="kimi",
                platform_name="Kimi",
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
AIClientFactory.register("kimi", KimiClient)