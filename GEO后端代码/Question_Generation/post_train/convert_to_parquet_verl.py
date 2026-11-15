"""
将 grpo_data_verl.jsonl 和 grpo_val_data.jsonl 转换为 verl GRPO 所需的 parquet 格式。

verl 要求数据包含以下列:
  - prompt:        list[dict], 聊天消息格式 [{"role": "user", "content": "..."}]
  - data_source:   str, 数据来源标识 (用于路由到对应的 reward function)
  - reward_model:  dict, 至少包含 {"ground_truth": "..."} 字段

在服务器上运行:
    cd /data/ypq/cyf/Question_Generation/post_train
    python convert_to_parquet_verl.py
"""
import json
import pandas as pd


def convert(jsonl_path: str, parquet_path: str):
    rows = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line.strip())

            # 原始 prompt 是纯文本，需要包装成 chat message 格式
            raw_prompt = item.get("prompt", "")
            brand_name = item.get("brand_name", "")

            chat_prompt = [{"role": "user", "content": raw_prompt}]

            new_row = {
                "prompt": chat_prompt,
                "data_source": "question_generation",       # 统一标识，reward function 据此路由
                "reward_model": {"ground_truth": brand_name},  # ground_truth 传给 reward 函数
                "extra_info": {"brand_name": brand_name},    # 额外信息，可被 reward 函数使用
            }
            rows.append(new_row)

    df = pd.DataFrame(rows)
    df.to_parquet(parquet_path, index=False)
    print(f"{jsonl_path} -> {parquet_path} ({len(df)} rows, columns: {list(df.columns)})")


if __name__ == "__main__":
    convert("grpo_data_verl.jsonl", "grpo_data_verl.parquet")
    convert("grpo_val_data.jsonl", "grpo_val_data.parquet")
