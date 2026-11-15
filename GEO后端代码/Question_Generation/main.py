"""
品牌推荐问题生成系统
运行模式：
1. crawl - 爬取数据并生成问题(完整流程): run_full_pipeline_from_crawl
2. add - 增量添加数据到知识库
3. remove - 从知识库删除指定数据
4. update - 更新指定数据
5. list - 查看知识库内容和统计
6. generate - 直接从已有知识库生成问题(无需传入文件):run_question_generation_from_kb
"""
import json
import argparse
from pathlib import Path
import copy
from datetime import datetime
from typing import List
from config.settings import settings
from config.crawler_config import get_brand_crawler_configs
from core.graph import run_full_pipeline_from_crawl, run_question_generation_from_kb
from agents.kb_management_agent import KBManagementAgent, list_kb

# action="store_true"传参就是True不传就是False
def main():
    parser = argparse.ArgumentParser(description="品牌推荐问题生成系统")
    parser.add_argument("--mode", type=str, choices=["crawl", "add", "remove", "update", "list", "generate"], default="crawl", help="运行模式: crawl(爬取生成), add(增量添加), remove(删除), update(更新), list(查看), generate(使用已有数据生成)")
    # 通用参数
    parser.add_argument("--brand", type=str, required=True, help="品牌名称")
    parser.add_argument("--domain", type=str, required=True, choices=["medicine", "electronics", "food", "fashion"], help="领域类型: medicine(药品), electronics(电子), food(食品), fashion(服装)")
    # crawl模式参数
    parser.add_argument("--competitors", type=str, default=None, help="竞品列表，逗号分隔（可选，如：'红花油,跌打损伤喷雾')")
    parser.add_argument("--output", type=str, default="output/question_pairs.json", help="输出文件路径" )
    parser.add_argument("--incremental-output", type=str, default="output/incremental/", help="增量输出目录")
    parser.add_argument("--max-accumulated", type=int, default=100, help="增量保存频率(每N个问题保存一次)")
    # add/update模式参数
    parser.add_argument("--source-type", type=str, default=None, choices=["official_site", "zhihu", "xiaohongshu", "whitepaper", "pdf", "json"], help="数据来源类型")
    parser.add_argument("--source", type=str, default=None, help="数据源:文件路径或URL")
    # remove模式参数
    parser.add_argument("--source-url", type=str, default=None, help="按URL删除")
    parser.add_argument("--doc-id", type=str, default=None, help="按doc_id删除")
    parser.add_argument("--parent-doc-id", type=str, default=None, help="按父doc_id删除所有分块")
    parser.add_argument("--force", action="store_true", help="强制删除无需确认")
    # list模式参数
    parser.add_argument("--detail", action="store_true", help="显示详细内容")
    parser.add_argument("--limit", type=int, default=20, help="结果数量限制")
    parser.add_argument("--format", type=str, default="summary", choices=["summary", "table", "json"], help="输出格式")
    # GEO分析参数
    parser.add_argument("--include-geo", action="store_true", help="启用GEO追踪分析（调用各AI平台分析品牌可见性）")

    args = parser.parse_args()

    # 解析竞品列表(自定义函数) 字符串 -> 列表，支持默认配置
    competitors = parse_competitors(args.competitors, args.brand, args.domain)

    # 路由到各模式处理器
    if args.mode == "crawl":
        run_crawl_mode(args.brand, args.domain, competitors, args.output, args.incremental_output, args.max_accumulated, args.include_geo)
    elif args.mode == "add":
        run_add_mode(args)
    elif args.mode == "remove":
        run_remove_mode(args)
    elif args.mode == "update":
        run_update_mode(args)
    elif args.mode == "list":
        run_list_mode(args)
    elif args.mode == "generate":
        run_generate_mode(args.brand, args.domain, competitors, args.output, args.incremental_output, args.max_accumulated, args.include_geo)

def parse_competitors(competitors_str: str, brand_name: str = None, domain_name: str = None) -> List[str]:
    """
    解析竞品列表

    Args:
        competitors_str: 命令行传入的竞品字符串（逗号分隔）
        brand_name: 品牌名称（用于读取默认配置）
        domain_name: 领域名称（用于读取默认配置）

    Returns:
        竞品列表
    """
    # 如果命令行指定了竞品，优先使用
    if competitors_str:
        return [c.strip() for c in competitors_str.split(',') if c.strip()]

    # 否则从默认配置文件读取
    if brand_name and domain_name:
        config_path = Path("data/domain_configs/competitors.json")
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                domain_config = config.get(domain_name, {})
                default_competitors = domain_config.get(brand_name, [])
                if default_competitors:
                    print(f"[INFO] 使用默认竞品配置: {default_competitors}")
                    return default_competitors
            except Exception as e:
                print(f"[WARN] 读取竞品配置失败: {e}")

    return []

def run_crawl_mode(brand_name: str, domain_name: str, competitors: List[str], output_path: str, incremental_output_path: str, max_accumulated_pairs: int = 100, include_geo: bool = False):
    """爬取模式：爬取数据并生成问题"""
    print(f"[INFO] 开始爬取数据，品牌: {brand_name}, 领域: {domain_name}")
    print(f"[INFO] 竞品列表: {competitors if competitors else '无'}")
    print(f"[INFO] GEO追踪分析: {'启用' if include_geo else '禁用'}")
    # 加载爬取配置
    crawl_config = get_brand_crawler_configs(brand_name)
    # 运行完整流程
    final_state = run_full_pipeline_from_crawl(brand_name=brand_name, domain_name=domain_name, crawl_config=crawl_config, competitors=competitors,
                                                max_accumulated_pairs=max_accumulated_pairs, incremental_output_path=incremental_output_path, include_geo=include_geo)
    # 格式化输出
    output_result = format_output(final_state, brand_name, competitors)
    # 保存输出
    save_output(output_result, output_path)
    # 打印输出总结
    print_summary(output_result)

def run_add_mode(args):
    """增量添加模式：添加数据到已有知识库"""
    brand_name = args.brand
    domain_name = args.domain
    source_type = args.source_type
    source = args.source
    print(f"[INFO] 增量添加数据，品牌: {brand_name}, 领域: {domain_name}, 来源类型: {source_type}")

    # 准备source_config
    source_config = {}
    if source_type in ["pdf", "json"]:
        source_config = {"source_path": source}
    else:
        source_config = {"enabled": True, "search_keyword": brand_name, "max_items": 10}
        if source_type == "official_site":
            source_config["base_url"] = source
            source_config["target_pages"] = [{"path": "/", "category": "品牌介绍"}]
            source_config["max_pages"] = 10

    # 执行添加操作
    agent = KBManagementAgent()
    state = agent.execute({"brand_name": brand_name, "domain_name": domain_name, "kb_operation_type": "add", "source_type": source_type, "source_config": source_config})
    result = state.get("kb_operation_result", {})

    if result.get("success"):
        print(f"[SUCCESS] 成功添加 {result.get('added_count', 0)} 个文档块")
        print(f"[INFO] Collection: {result.get('collection_name')}")
        if result.get("duplicates_skipped", 0) > 0:
            print(f"[INFO] 跳过 {result.get('duplicates_skipped', 0)} 个重复文档")
    else:
        print(f"[WARN] 添加结果: {result.get('message', 'Unknown error')}")


def run_remove_mode(args):
    """
    删除模式：从知识库删除指定数据
    """
    brand_name = args.brand
    source_type = args.source_type
    source_url = args.source_url
    doc_id = args.doc_id
    parent_doc_id = args.parent_doc_id
    force = args.force

    print(f"[INFO] 删除数据，品牌: {brand_name}")

    # 确认删除（除非force）
    if not force:
        # 预览将要删除的数据
        preview_result = list_kb(brand_name, detail=True, source_type=source_type)
        if preview_result.get("statistics", {}).get("total_entities", 0) > 0:
            docs = preview_result.get("documents", [])
            print(f"[INFO] 将删除匹配的文档（共 {len(docs)} 个）")
            for doc in docs[:5]:
                print(f"  - {doc.get('doc_id')}: {doc.get('source_title', '')[:30]}...")
            if len(docs) > 5:
                print(f"  ... 还有 {len(docs) - 5} 个")
            confirm = input("确认删除？(y/n): ")
            if confirm.lower() != 'y':
                print("[INFO] 操作取消")
                return
        else:
            print("[INFO] 没有找到匹配的文档")
            return

    # 执行删除操作
    agent = KBManagementAgent()
    state = agent.execute({"brand_name": brand_name, "kb_operation_type": "remove", "remove_source_type": source_type,
                            "remove_source_url": source_url, "remove_doc_id": doc_id, "remove_parent_doc_id": parent_doc_id})

    result = state.get("kb_operation_result", {})
    print(f"[SUCCESS] 成功删除 {result.get('deleted_count', 0)} 个文档")


def run_update_mode(args):
    """更新模式：删除旧版本 + 添加新版本"""
    brand_name = args.brand
    domain_name = args.domain
    source_type = args.source_type
    source_url = args.source_url
    new_source = args.source

    print(f"[INFO] 更新数据，品牌: {brand_name}, 领域: {domain_name}")

    # 准备新数据配置
    new_source_config = {}
    if source_type in ["pdf", "json"]:
        new_source_config = {"source_path": new_source}
    else:
        new_source_config = {
            "enabled": True,
            "search_keyword": brand_name,
            "max_items": 10,
        }
        if source_type == "official_site":
            new_source_config["base_url"] = new_source
            new_source_config["target_pages"] = [{"path": "/", "category": "品牌介绍"}]
            new_source_config["max_pages"] = 10

    # 执行更新操作
    agent = KBManagementAgent()
    state = agent.execute({"brand_name": brand_name, "domain_name": domain_name, "kb_operation_type": "update", "source_type": source_type, "remove_source_url": source_url, "source_config": new_source_config})
    result = state.get("kb_operation_result", {})
    print(f"[SUCCESS] 更新完成")
    remove_result = result.get("remove_result", {})
    add_result = result.get("add_result", {})
    print(f"  - 删除: {remove_result.get('deleted_count', 0)} 个文档")
    print(f"  - 添加: {add_result.get('added_count', 0)} 个文档")

def run_list_mode(args):
    """
    查看模式：显示知识库内容和统计
    """
    brand_name = args.brand
    source_type = args.source_type
    detail = args.detail
    limit = args.limit
    format_type = args.format

    print(f"[INFO] 知识库统计，品牌: {brand_name}")

    agent = KBManagementAgent()
    state = agent.execute({"brand_name": brand_name, "kb_operation_type": "list", "list_source_type": source_type,
                            "list_detail": detail, "list_limit": limit, "list_format": format_type})
    result = state.get("kb_operation_result", {})
    stats = result.get("statistics", {})

    if format_type == "summary":
        print("\n" + "=" * 60)
        print("知识库统计摘要")
        print("=" * 60)
        print(f"Collection: {result.get('collection_name')}")
        print(f"总文档数: {stats.get('total_entities', 0)}")
        print(f"平均质量评分: {stats.get('avg_quality_score', 0):.2f}")

        print("\n按来源类型分布:")
        for st, info in stats.get("by_source_type", {}).items():
            print(f"  {st}: {info.get('count')} 个 (平均质量: {info.get('avg_quality', 0):.2f})")

        print("\n按内容分类分布:")
        for cat, count in stats.get("by_category", {}).items():
            print(f"  {cat}: {count} 个")
        print("=" * 60)

    elif format_type == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif format_type == "table" and detail:
        docs = result.get("documents", [])
        print("\n文档列表:")
        for doc in docs[:limit]:
            print(f"  ID: {doc.get('id')}")
            print(f"  URL: {doc.get('source_url', '')[:60]}")
            print(f"  类型: {doc.get('source_type')} | 分类: {doc.get('category')}")
            print(f"  质量: {doc.get('quality_score', 0):.2f}")
            # 显示内容摘要（前300字符）
            content = doc.get('original_content', '')
            if content:
                summary = content[:300].replace('\n', ' ')
                print(f"  内容: {summary}...")
            print("-" * 60)

def run_generate_mode(brand_name: str, domain_name: str, competitors: List[str], output_path: str, incremental_output_path: str = "output/incremental/", max_accumulated_pairs: int = 100, include_geo: bool = False):
    """
    生成模式：直接使用已有知识库生成问题 流程：连接 Milvus 获取已有数据 -> 逐块生成问题 -> 批量评估
    """
    print(f"[INFO] 开始生成问题，品牌: {brand_name}, 领域: {domain_name}")
    print(f"[INFO] GEO追踪分析: {'启用' if include_geo else '禁用'}")

    # 自动获取 collection_name
    collection_name = settings.get_external_collection_name(brand_name)

    print(f"[INFO] 使用知识库: {collection_name}")

    # 检查知识库是否存在且有数据
    from vectorstore.milvus_client import MilvusClient
    milvus_client = MilvusClient(collection_name=collection_name)

    try:
        stats = milvus_client.get_collection_stats()
        total_blocks = stats.get("num_entities", 0)
        if total_blocks == 0:
            print(f"[ERROR] 知识库 {collection_name} 中没有数据")
            print(f"[提示] 请先使用 crawl 或 add 模式添加数据")
            return
        print(f"[INFO] 知识库共有 {total_blocks} 个文档块")
    except Exception as e:
        print(f"[ERROR] 无法连接知识库: {str(e)}")
        print(f"[提示] 请确保 Milvus 服务已启动")
        return

    # 运行问题生成流程（直接从知识库）
    final_state = run_question_generation_from_kb(brand_name=brand_name, domain_name=domain_name, competitors=competitors, max_accumulated_pairs=max_accumulated_pairs, incremental_output_path=incremental_output_path, include_geo=include_geo)
    if final_state is None:
        print("[ERROR] 问题生成失败")
        return
    # 格式化输出
    output_result = format_output(final_state, brand_name, competitors)
    # 保存输出
    save_output(output_result, output_path)
    print_summary(output_result)

def format_output(state: dict, brand_name: str, competitors: List[str]) -> dict:
    """格式化输出结果"""
    question_pairs = state.get("question_pairs", [])
    evaluation_summary = state.get("question_evaluation_summary")
    geo_summary = state.get("geo_summary")
    formatted_questions = []

    for qp in question_pairs:
        formatted_questions.append({"id": qp["id"], "block_id": qp["block_id"], "brand_name": qp["brand_name"], "competitors": qp["competitors"],
            "primary_question": qp["primary_question"], "question_type": qp["question_type"], "target_entity": qp["target_entity"],
            "rewritten_questions": qp["rewritten_questions"], "entity_tags": qp["entity_tags"], "relation_types": qp["relation_types"],
            "source_text": qp["source_text"], "evaluation_metrics": qp.get("evaluation_metrics"), "created_at": qp["created_at"]})

    return {"brand_name": brand_name, "competitors": competitors, "generated_at": datetime.now().isoformat(), "question_pairs": formatted_questions,
            "evaluation_summary": evaluation_summary,
            "geo_summary": geo_summary,
        "statistics": {"total_blocks": evaluation_summary.get("total_blocks", 0) if evaluation_summary else len(formatted_questions),
            "total_questions": len(formatted_questions), "total_rewritten_questions": sum(len(q["rewritten_questions"]) for q in formatted_questions),
            "brand_leak_rate": evaluation_summary.get("brand_leak_rate", 0) if evaluation_summary else 0}}


def save_output(output_result: dict, output_path: str):
    """保存输出（指定字段写成一行）"""
    from pathlib import Path
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 需要写成一行紧凑格式的字段
    compact_fields = ["competitors_found", "competitor_ranks_avg", "mention_positions", "sentiment_distribution"]
    
    # 预处理 geo_summary 中指定字段
    processed = copy.deepcopy(output_result)
    geo = processed.get("geo_summary")
    if geo is None:
        geo = {}
    processed["geo_summary"] = geo
    if "platform_stats" in geo:
        for platform, stats in geo["platform_stats"].items():
            for field in compact_fields:
                if field in stats and not isinstance(stats[field], str):
                    stats[field] = json.dumps(stats[field], ensure_ascii=False)
            if "competitor_details_summary" in stats and isinstance(stats["competitor_details_summary"], dict):
                comp_details = stats["competitor_details_summary"]
                pairs = []
                for brand, data in comp_details.items():
                    pairs.append(json.dumps(brand, ensure_ascii=False) + ": " + json.dumps(data, ensure_ascii=False))
                stats["competitor_details_summary"] = "{" + ", ".join(pairs) + "}"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)
    print("[INFO] 结果已保存至: {}".format(output_path))


def print_summary(output_result: dict):
    """打印汇总信息"""
    stats = output_result.get("statistics", {})
    summary = output_result.get("evaluation_summary", {})
    geo_summary = output_result.get("geo_summary")

    print("\n" + "=" * 60)
    print("[生成完成] 问题生成汇总")
    print("=" * 60)
    print(f"品牌名称: {output_result.get('brand_name')}")
    print(f"竞品列表: {output_result.get('competitors')}")
    print(f"处理的文本块数: {stats.get('total_blocks', 0)}")
    print(f"生成的主问题数: {stats.get('total_questions', 0)}")
    print(f"生成的改写问题数: {stats.get('total_rewritten_questions', 0)}")

    if summary:
        print("\n[评估结果]")
        print(f"平均客观得分: {summary.get('avg_objective_score', 0)}")
        print(f"平均主观得分: {summary.get('avg_subjective_score', 0)}")
        print(f"平均综合得分: {summary.get('avg_total_score', 0)}")
        print(f"品牌泄露率: {summary.get('brand_leak_rate', 0)}%")

        print("\n[问题类型分布]")
        for q_type, count in summary.get("questions_by_type", {}).items():
            print(f"  {q_type}: {count}")

    # GEO分析结果
    if geo_summary:
        print("\n" + "=" * 60)
        print("[GEO追踪分析完整结果]")
        print("=" * 60)
        print(f"分析的文本块数: {geo_summary.get('total_blocks', 0)}")
        print(f"分析的问题总数: {geo_summary.get('total_questions', 0)}")
        print(f"总分析次数: {geo_summary.get('total_analyses', 0)}")

        # API调用失败统计
        api_failure_count = geo_summary.get('api_failure_count', 0)
        if api_failure_count > 0:
            print(f"\n[API调用失败统计]")
            print(f"失败次数: {api_failure_count}")
            for err in geo_summary.get('api_failure_errors', [])[:5]:
                print(f"  - 平台 {err.get('platform')}: {err.get('error')}")

        print("\n[各平台完整指标（独立统计）]")
        platform_stats = geo_summary.get("platform_stats", {})
        for platform, p_stats in platform_stats.items():
            print(f"\n=== {platform} ===")
            print(f"  基础指标:")
            print(f"    总分析次数: {p_stats.get('total_count', 0)}")
            print(f"    提及次数(有无): {p_stats.get('mentioned_count', 0)}")
            print(f"    总提及次数: {p_stats.get('total_mention_count', 0)}")
            print(f"    提及率: {p_stats.get('mention_rate', 0):.2%}")
            print(f"    平均排名: {p_stats.get('avg_rank', 0):.2f}")

            # 提及位置分布
            mention_positions = p_stats.get('mention_positions', {})
            if mention_positions:
                print(f"  提及位置分布:")
                print(f"    醒目位置(prominent): {mention_positions.get('prominent', 0)}")
                print(f"    较早位置(early): {mention_positions.get('early', 0)}")
                print(f"    中间位置(middle): {mention_positions.get('middle', 0)}")
                print(f"    较晚位置(late): {mention_positions.get('late', 0)}")

            print(f"  情感分析:")
            print(f"    平均情感值: {p_stats.get('avg_sentiment', 0):.2f}")
            # 情感分布
            sentiment_dist = p_stats.get('sentiment_distribution', {})
            if sentiment_dist:
                print(f"    情感分布:")
                print(f"      正面(positive): {sentiment_dist.get('positive', 0)}")
                print(f"      中性(neutral): {sentiment_dist.get('neutral', 0)}")
                print(f"      负面(negative): {sentiment_dist.get('negative', 0)}")

            print(f"  引用分析:")
            print(f"    平均权威度: {p_stats.get('authority_avg', 0):.2f}")
            print(f"    品牌官网引用次数: {p_stats.get('brand_website_cited_count', 0)}")
            brand_citations = p_stats.get('brand_citations', [])
            if brand_citations:
                print(f"    品牌引用源: {brand_citations[:5]}...")
            # 引用类型分布
            citation_types = p_stats.get('citation_types_summary', {})
            if citation_types:
                print(f"    引用类型分布:")
                for t, count in citation_types.items():
                    print(f"      {t}: {count}")

            print(f"  竞品分析:")
            competitors_found = p_stats.get('competitors_found', [])
            if competitors_found:
                print(f"    发现的竞品: {competitors_found}")
            competitor_ranks_avg = p_stats.get('competitor_ranks_avg', {})
            if competitor_ranks_avg:
                print(f"    竞品平均排名: {competitor_ranks_avg}")
            # 竞品详情汇总
            competitor_details = p_stats.get('competitor_details_summary', {})
            if competitor_details:
                print(f"    竞品详情汇总:")
                for comp, details in competitor_details.items():
                    print(f"      {comp}:")
                    print(f"        提及次数: {details.get('mention_count', 0)}")
                    print(f"        平均排名: {details.get('avg_rank', 0):.2f}")
                    avg_sentiment = details.get('avg_sentiment', 0)
                    sentiment_label = "正面" if avg_sentiment > 0.3 else ("负面" if avg_sentiment < -0.3 else "中性")
                    print(f"        平均情感: {avg_sentiment:.2f} ({sentiment_label})")
            competitor_citations = p_stats.get('competitor_citations_summary', {})
            if competitor_citations:
                for comp, cites in competitor_citations.items():
                    print(f"    {comp}引用源: {cites[:3]}...")

            # 回答样例
            answer_samples = p_stats.get('answer_samples', [])
            if answer_samples:
                print(f"  回答样例(前500字符):")
                for i, ans in enumerate(answer_samples[:2], 1):
                    print(f"    样例{i}: {ans[:200]}...")

        # 图表路径
        chart_paths = geo_summary.get('chart_paths', {})
        if chart_paths:
            print("\n[生成的图表]")
            for chart_name, chart_path in chart_paths.items():
                print(f"  {chart_name}: {chart_path}")

        # 优化建议
        recommendations = geo_summary.get('recommendations', [])
        if recommendations:
            print("\n[优化建议]")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"  {i}. [{rec.get('priority', '中')}] {rec.get('category', '')}: {rec.get('suggestion', rec.get('action', ''))}")

    print("=" * 60)


if __name__ == "__main__":
    main()  