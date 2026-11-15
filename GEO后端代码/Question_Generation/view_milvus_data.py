#!/usr/bin/env python3
"""
查看 Milvus 数据库内容

用法：
    nohup python -u view_milvus_data.py --brand 君乐宝 >| /root/workspace/Question_Generation/milvus_output.log 2>&1 &
    python view_milvus_data.py --brand 君乐宝 --collection external_kb
    python view_milvus_data.py --brand 君乐宝 --collection geo_analysis
    python view_milvus_data.py --brand 君乐宝 --limit 10
"""

import argparse
import json
from datetime import datetime
from pymilvus import connections, utility, Collection


def connect_milvus(db_path="./milvus_data/milvus.db"):
    connections.connect(uri=db_path)


def disconnect_milvus():
    try:
        connections.disconnect("default")
    except:
        pass


def get_all_collections():
    return utility.list_collections()


def get_collection_fields(coll_name):
    coll = Collection(coll_name)
    return [f.name for f in coll.schema.fields]


def view_external_kb(brand, limit=None, output_fields=None):
    """查看 external_kb_{brand} Collection"""
    coll_name = f"external_kb_{brand}"

    if not utility.has_collection(coll_name):
        print("[错误] Collection {} 不存在".format(coll_name))
        return

    coll = Collection(coll_name)
    coll.load()

    print("\n" + "="*60)
    print("Collection: {}".format(coll_name))
    print("="*60)

    all_fields = get_collection_fields(coll_name)
    print("字段: {}".format(all_fields))

    total = coll.num_entities
    print("总记录数: {}".format(total))

    if output_fields is None:
        output_fields = [f for f in all_fields if f != "embedding"]  # 排除embedding向量（太长）

    if limit:
        results = coll.query(expr="", output_fields=output_fields, limit=limit)
    else:
        results = coll.query(expr="", output_fields=output_fields, limit=total)

    print("\n--- 数据内容 ---")
    for i, r in enumerate(results):
        print("\n[记录 {}]".format(i+1))
        for k, v in r.items():
            if isinstance(v, str):
                print("  {}: {} (共{}字符)".format(k, v, len(v)))
            elif isinstance(v, (list, dict)):
                v_str = json.dumps(v, ensure_ascii=False)
                print("  {}: {} (共{}字符)".format(k, v_str, len(v_str)))
            else:
                print("  {}: {}".format(k, v))

    return results


def view_geo_analysis(brand, limit=None, output_fields=None):
    """查看 geo_analysis_{brand} Collection"""
    coll_name = f"geo_analysis_{brand}"

    if not utility.has_collection(coll_name):
        print("[错误] Collection {} 不存在".format(coll_name))
        return

    coll = Collection(coll_name)
    coll.load()

    print("\n" + "="*60)
    print("Collection: {}".format(coll_name))
    print("="*60)

    all_fields = get_collection_fields(coll_name)
    print("字段: {}".format(all_fields))

    total = coll.num_entities
    print("总记录数: {}".format(total))

    if output_fields is None:
        output_fields = [f for f in all_fields if f != "question_embedding"]  # 排除embedding向量（太长）

    if limit:
        results = coll.query(expr="", output_fields=output_fields, limit=limit)
    else:
        results = coll.query(expr="", output_fields=output_fields, limit=total)

    # 统计信息
    mentioned_true = sum(1 for r in results if r.get("mentioned") == True)
    mentioned_false = total - mentioned_true
    avg_rank = sum(r.get("rank", 0) for r in results if r.get("mentioned") == True) / mentioned_true if mentioned_true > 0 else 0

    print("\n--- 统计 ---")
    print("  mentioned=True: {}".format(mentioned_true))
    print("  mentioned=False: {}".format(mentioned_false))
    print("  平均排名(仅提及): {:.2f}".format(avg_rank))

    has_citations = sum(1 for r in results if r.get("brand_citations") and len(str(r.get("brand_citations", ""))) > 10)
    print("  有引用的记录: {}".format(has_citations))

    print("\n--- 数据内容 ---")
    for i, r in enumerate(results):
        print("\n[记录 {}]".format(i+1))
        for k, v in r.items():
            if isinstance(v, str):
                print("  {}: {} (共{}字符)".format(k, v, len(v)))
            elif isinstance(v, (list, dict)):
                v_str = json.dumps(v, ensure_ascii=False)
                print("  {}: {} (共{}字符)".format(k, v_str, len(v_str)))
            else:
                print("  {}: {}".format(k, v))

    return results


def view_all_collections(brand, limit=None):
    print("\n" + "="*60)
    print("Milvus 数据库内容查看")
    print("品牌: {}".format(brand))
    print("="*60)

    all_colls = get_all_collections()
    print("\n所有 Collection: {}".format(all_colls))

    view_external_kb(brand, limit)
    view_geo_analysis(brand, limit)


def main():
    parser = argparse.ArgumentParser(description="查看 Milvus 数据库内容")
    parser.add_argument("--brand", type=str, required=True, help="品牌名称")
    parser.add_argument("--collection", type=str, choices=["external_kb", "geo_analysis", "all"], default="all", help="Collection 类型")
    parser.add_argument("--limit", type=int, default=None, help="限制输出数量")
    parser.add_argument("--db", type=str, default="./milvus_data/milvus.db", help="Milvus 数据库路径")

    args = parser.parse_args()

    connect_milvus(args.db)

    try:
        if args.collection == "external_kb":
            view_external_kb(args.brand, args.limit)
        elif args.collection == "geo_analysis":
            view_geo_analysis(args.brand, args.limit)
        else:
            view_all_collections(args.brand, args.limit)
    finally:
        disconnect_milvus()


if __name__ == "__main__":
    main()

# nohup python -u view_milvus_data.py --brand 华为 >| /root/workspace/Question_Generation/milvus_output.log 2>&1 &