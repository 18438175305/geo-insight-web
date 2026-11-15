"""
修复 Qwen2.5 tokenizer_config.json 的 extra_special_tokens 字段。
将 "extra_special_tokens": [] 改为 "extra_special_tokens": {}

使用方法:
    python fix_tokenizer_config.py
"""
import json
import sys

TOKENIZER_CONFIG = "/data/ypq/cyf/Question_Generation/models/Qwen2.5-7B-Instruct-SFT_0602/tokenizer_config.json"

with open(TOKENIZER_CONFIG, "r", encoding="utf-8") as f:
    config = json.load(f)

old_value = config.get("extra_special_tokens")
print(f"修复前: extra_special_tokens = {old_value!r} (type: {type(old_value).__name__})")

if isinstance(old_value, list):
    config["extra_special_tokens"] = {}
    with open(TOKENIZER_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"修复后: extra_special_tokens = {{}} (dict)")
    print("tokenizer_config.json 已修复!")
else:
    print("extra_special_tokens 已经是 dict 类型，无需修复。")
