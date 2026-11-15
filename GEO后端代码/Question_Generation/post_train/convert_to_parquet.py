"""
将 grpo_data_verl.jsonl 和 grpo_val_data.jsonl 转换为 VERL 所需的 parquet 格式。
在服务器上运行: python convert_to_parquet.py
"""
import json
import pandas as pd


def convert(jsonl_path, parquet_path):
    rows = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line.strip()))
    df = pd.DataFrame(rows)
    df.to_parquet(parquet_path, index=False)
    print(f"{jsonl_path} -> {parquet_path} ({len(df)} rows, columns: {list(df.columns)})")


if __name__ == "__main__":
    convert("grpo_data_verl.jsonl", "grpo_data_verl.parquet")
    convert("grpo_val_data.jsonl", "grpo_val_data.parquet")
