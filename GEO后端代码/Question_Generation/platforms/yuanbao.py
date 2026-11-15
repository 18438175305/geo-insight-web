"""
元宝 (Yuanbao) API客户端

腾讯混元 API文档: https://cloud.tencent.com/document/product/1729
"""

import os
import hashlib
import time
import hmac
import json
from typing import List, Optional
from platforms.base import BaseAIClient, AIResponse, AIClientFactory, PLATFORMS
from config.settings import settings


class YuanbaoClient(BaseAIClient):
    """元宝 API客户端"""

    def __init__(self, api_key: str = None, secret_key: str = None, model: str = None):
        # 从配置读取
        platform_config = PLATFORMS.get("yuanbao", {})
        api_key = api_key or os.environ.get(platform_config.get("api_key_env", "YUANBAO_API_KEY"))
        secret_key = secret_key or os.environ.get(platform_config.get("secret_key_env", "YUANBAO_SECRET_KEY"))
        if not api_key:
            # 从 settings.geo_tracking 获取
            api_key = settings.geo_tracking.yuanbao_api_key
        if not api_key:
            raise ValueError("缺少YUANBAO_API_KEY，请设置环境变量")

        model = model or platform_config.get("default_model", "hunyuan-lite")
        api_base = platform_config.get("api_base", "https://hunyuan.tencentcloudapi.com")

        super().__init__(
            api_key=api_key,
            api_base=api_base,
            model=model
        )
        self.secret_key = secret_key or ""

    def query(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        use_cache=None,
    ) -> AIResponse:
        """调用元宝 API获取回复"""

        # 腾讯混元需要特殊签名
        timestamp = int(time.time())
        signature = self._generate_signature(timestamp)

        headers = {
            "Content-Type": "application/json",
            "Authorization": signature,
            "X-TC-Action": "ChatCompletions",
            "X-TC-Version": "2023-09-01",
            "X-TC-Timestamp": str(timestamp),
        }

        data = {
            "Model": self.model,
            "Messages": [{"Role": "user", "Content": prompt}],
            "MaxTokens": max_tokens,
            "Temperature": temperature,
        }

        try:
            response = self._make_request(
                self.api_base,
                headers=headers,
                data=data,
            )

            if response.status_code != 200:
                return AIResponse(
                    platform="yuanbao",
                    platform_name="元宝",
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
            response_data = result.get("Response", {})
            choices = response_data.get("Choices", [{}])
            content = choices[0].get("Message", {}).get("Content", "")
            citations = self._extract_urls_from_text(content)

            return AIResponse(
                platform="yuanbao",
                platform_name="元宝",
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
                platform="yuanbao",
                platform_name="元宝",
                prompt=prompt,
                content="",
                citations=[],
                success=False,
                error=str(e),
                latency=0,
                cached=False,
                raw_response=None,
            )

    def _generate_signature(self, timestamp: int) -> str:
        """生成腾讯API签名"""
        if not self.secret_key:
            return ""
        # 简化的签名生成
        sign_str = f"{self.api_key}{timestamp}"
        signature = hmac.new(
            self.secret_key.encode(),
            sign_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature


# 注册到工厂
AIClientFactory.register("yuanbao", YuanbaoClient)