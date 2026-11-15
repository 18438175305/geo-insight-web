"""
Prompt模板加载器，所有prompt已外置到 data/prompts/ 目录下的 .md 文件

支持领域特定配置动态加载：
- KG抽取: kg_extraction_{domain}.md
- 问题生成: question_generation.md + domain_configs/question_types.json
"""
from pathlib import Path
from typing import Dict
import json

# 缓存
_prompt_cache: Dict[str, str] = {}
_domain_config_cache: Dict[str, Dict] = {}

# Prompt文件目录
PROMPTS_DIR = "data/prompts"
DOMAIN_CONFIGS_DIR = "data/domain_configs"


def load_prompt(prompt_name: str) -> str:
    """
    加载指定的prompt模板

    Args:
        prompt_name: prompt文件名
            - 问题生成: "question_generation"
            - 问题改写: "question_rewrite"
            - 问题评估: "question_quality_eval"
            - 文本清洗: "text_cleaning"
            - KG抽取: "kg_extraction_medicine", "kg_extraction_electronics", "kg_extraction_food", "kg_extraction_fashion"

    Returns:
        prompt模板字符串

    Raises:
        FileNotFoundError: prompt文件不存在
    """
    cache_key = prompt_name
    if cache_key in _prompt_cache:
        return _prompt_cache[cache_key]

    prompt_file = Path(PROMPTS_DIR) / f"{prompt_name}.md"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read()
        if not prompt:
            raise ValueError(f"Prompt file is empty: {prompt_file}")

        _prompt_cache[cache_key] = prompt
        return prompt

    except Exception as e:
        raise RuntimeError(f"Failed to load prompt {prompt_name}: {e}")


def load_domain_question_types(domain_name: str) -> str:
    """
    加载领域特定的问题类型配置，格式化为Prompt文本

    Args:
        domain_name: 领域名称 (medicine/electronics/food/fashion)

    Returns:
        格式化后的领域问题类型说明文本
    """
    if domain_name in _domain_config_cache:
        return _domain_config_cache[domain_name]

    config_file = Path(DOMAIN_CONFIGS_DIR) / "question_types.json"
    if not config_file.exists():
        # 如果配置文件不存在，返回默认问题类型
        return get_default_question_types()

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            all_configs = json.load(f)

        domain_config = all_configs.get(domain_name)
        if not domain_config:
            return get_default_question_types()

        # 格式化为Prompt文本
        formatted_text = format_domain_question_types(domain_config)
        _domain_config_cache[domain_name] = formatted_text
        return formatted_text

    except Exception as e:
        print(f"[WARN] Failed to load domain config: {e}")
        return get_default_question_types()


def format_domain_question_types(domain_config: Dict) -> str:
    """
    将领域配置格式化为Prompt文本

    Args:
        domain_config: 领域配置字典

    Returns:
        格式化后的文本
    """
    lines = []
    domain_name = domain_config.get("domain_name", "通用领域")
    lines.append(f"当前领域：{domain_name}")
    lines.append("")
    lines.append("可选问题类型：")

    question_types = domain_config.get("question_types", {})
    for type_name, type_config in question_types.items():
        template = type_config.get("template", "")
        examples = type_config.get("examples", [])
        constraint = type_config.get("constraint", "")

        lines.append(f"  【{type_name}】")
        lines.append(f"    模板：{template}")
        if examples:
            lines.append(f"    示例：")
            for ex in examples[:2]:
                lines.append(f"      - {ex}")
        if constraint:
            lines.append(f"    约束：{constraint}")
        lines.append("")

    return "\n".join(lines)


def get_default_question_types() -> str:
    """
    获取默认问题类型（当领域配置不存在时使用）

    Returns:
        默认问题类型文本
    """
    return """当前领域：通用领域

可选问题类型：
  【特征问询】
    模板：什么产品有...功效/特点？
    示例：
      - 什么产品有止血功效？

  【场景问询】
    模板：在...情况下用什么产品好？
    示例：
      - 外伤出血用什么产品好？

  【对比问询】
    模板：X和Y相比哪个更适合...？（如有竞品）
    示例：
      - A和B相比哪个效果更好？

  【推荐问询】
    模板：有什么产品推荐用于...？
    示例：
      - 有什么止血药推荐？
"""


def get_prompt(prompt_name: str, **kwargs) -> str:
    """
    加载并格式化prompt

    Args:
        prompt_name: prompt名称
        **kwargs: prompt模板中的变量

    Returns:
        格式化后的prompt字符串
    """
    template = load_prompt(prompt_name)

    # 如果是question_generation且有domain_name，加载领域配置
    if prompt_name == "question_generation" and "domain_name" in kwargs:
        domain_name = kwargs.get("domain_name", "")
        domain_question_types = load_domain_question_types(domain_name)
        kwargs["domain_question_types"] = domain_question_types

    return template.format(**kwargs)


def list_available_prompts() -> list:
    """列出所有可用的prompt文件"""
    prompts_dir = Path(PROMPTS_DIR)
    if not prompts_dir.exists():
        return []
    return [f.stem for f in prompts_dir.glob("*.md")]


def list_available_domains() -> list:
    """列出所有可用的领域配置"""
    config_file = Path(DOMAIN_CONFIGS_DIR) / "question_types.json"
    if not config_file.exists():
        return []
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            configs = json.load(f)
        return list(configs.keys())
    except Exception:
        return []