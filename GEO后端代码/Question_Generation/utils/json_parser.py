"""JSON解析工具 - 支持LLM返回的各种格式"""

import json
import re
from typing import Dict, List, Any, Optional, Union


def _preprocess_llm_response(response: str) -> str:
    """预处理LLM响应"""
    text = response.strip()
    # 移除markdown代码块标记
    text = re.sub(r"```(?:json)?\s*\n?", "", text)
    text = re.sub(r"```\s*$", "", text)
    # 移除模板占位符
    text = re.sub(r"\[请在此处填写\]", "[]", text)
    return text.strip()


def _fix_json_syntax(json_str: str) -> str:
    """修复常见JSON语法错误"""
    # 移除注释
    json_str = re.sub(r"//.*$", "", json_str, flags=re.MULTILINE)
    json_str = re.sub(r"/\*.*?\*/", "", json_str, flags=re.DOTALL)
    # 移除尾部逗号
    json_str = re.sub(r",\s*\]", "]", json_str)
    json_str = re.sub(r",\s*\}", "}", json_str)
    return json_str


def _find_balanced_json(text: str, start_char: str, end_char: str) -> Optional[str]:
    """找到平衡的JSON块"""
    start_idx = text.find(start_char)
    if start_idx == -1:
        return None

    depth = 0
    in_string = False
    escape_next = False

    for i in range(start_idx, len(text)):
        char = text[i]

        if escape_next:
            escape_next = False
            continue

        if char == chr(92) and in_string:  # backslash
            escape_next = True
            continue

        if char == chr(34) and not escape_next:  # double quote
            in_string = not in_string
            continue

        if not in_string:
            if char == start_char:
                depth += 1
            elif char == end_char:
                depth -= 1
                if depth == 0:
                    return text[start_idx:i + 1]

    # 尝试截取到最后一个闭合括号
    if depth > 0:
        last_close = text.rfind(end_char)
        if last_close > start_idx:
            return text[start_idx:last_close + 1]
    
    return None


def _extract_json_fragment(text: str) -> Optional[str]:
    """尝试多种方式提取JSON"""
    # 方式1: 直接查找
    result = _find_balanced_json(text, chr(123), chr(125))  # { }
    if result:
        return result
    
    # 方式2: 处理双花括号转义 {{ }}
    text_fixed = text.replace(chr(123)+chr(123), chr(123)).replace(chr(125)+chr(125), chr(125))
    result = _find_balanced_json(text_fixed, chr(123), chr(125))
    if result:
        return result
    
    # 方式3: 提取entities和relations
    entities_pattern = chr(34) + "entities" + chr(34) + r"\s*:\s*\[.*?\]"
    relations_pattern = chr(34) + "relations" + chr(34) + r"\s*:\s*\[.*?\]"
    
    e_match = re.search(entities_pattern, text, re.DOTALL)
    r_match = re.search(relations_pattern, text, re.DOTALL)
    
    if e_match or r_match:
        e_str = e_match.group(0) if e_match else chr(34) + "entities" + chr(34) + ": []"
        r_str = r_match.group(0) if r_match else chr(34) + "relations" + chr(34) + ": []"
        return chr(123) + e_str + ", " + r_str + chr(125)
    
    return None


def parse_json_object(response: str, default=None, verbose=False) -> Dict:
    """从文本解析JSON对象"""
    if default is None:
        default = {}

    text = _preprocess_llm_response(response)
    json_str = _extract_json_fragment(text)
    
    if json_str is None:
        if verbose:
            print(f"[WARN] No JSON found (len={len(response)})")
        return default
    
    json_str = _fix_json_syntax(json_str)
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        if verbose:
            print(f"[WARN] JSON error: {e}")
        return default


def parse_json_array(response: str, default=None, verbose=False) -> List:
    """从文本解析JSON数组"""
    if default is None:
        default = []

    text = _preprocess_llm_response(response)
    json_str = _find_balanced_json(text, chr(91), chr(93))  # [ ]
    
    if json_str is None:
        return default
    
    json_str = _fix_json_syntax(json_str)
    
    try:
        result = json.loads(json_str)
        return result if isinstance(result, list) else default
    except json.JSONDecodeError:
        return default


def safe_json_loads(text: str, default=None) -> Any:
    """安全JSON加载"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return default if default is not None else {}
