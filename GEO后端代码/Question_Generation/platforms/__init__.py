"""
AI平台API客户端模块

支持的主流公域AI平台:
- deepseek: DeepSeek
- qwen: 通义千问 (阿里云DashScope)
- kimi: Kimi (月之暗面Moonshot)
- doubao: 豆包 (字节跳动Volcengine)
- yuanbao: 元宝 (腾讯混元)

使用方式:
    from platforms import AIClientFactory

    client = AIClientFactory.create("deepseek")
    response = client.query("推荐新能源汽车品牌")
"""

# AIResponse 统一从 core.state 导入（通过 base 模块传递）
from platforms.base import AIResponse, BaseAIClient, AIClientFactory, InMemoryCache, PLATFORMS
from platforms.deepseek import DeepSeekClient
from platforms.qwen import QwenClient
from platforms.kimi import KimiClient
from platforms.doubao import DoubaoClient
from platforms.yuanbao import YuanbaoClient

__all__ = [
    "AIResponse",
    "BaseAIClient",
    "AIClientFactory",
    "InMemoryCache",
    "DeepSeekClient",
    "QwenClient",
    "KimiClient",
    "DoubaoClient",
    "YuanbaoClient",
    "PLATFORMS",
]