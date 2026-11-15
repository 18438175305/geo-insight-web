"""
批处理增量输出工具

用于解决记忆管理和上下文窗口问题：
1. 批处理模式：每批爬取文档处理完立即保存，释放内存
2. 增量模式：问题对增量保存，支持大规模数据处理（10万+文本块）
3. 支持增量加载已保存的数据
4. 最后合并所有增量输出为最终结果
5. 每次运行使用独立的批次目录（时间戳命名），区分不同运行

包含两类功能：
- batch_output: 处理爬取文档（文档、KG数据）
- incremental_output: 处理问题对（问题对、统计数据）
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from core.state import CrawledDocumentState
from kg_extraction.kg_schema import KGEntity, KGRelation, KGTriple


# ============================================================
# 批次ID管理
# ============================================================

def generate_run_id() -> str:
    """生成运行批次ID（时间戳格式）"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def get_batch_output_path(base_path: str, run_id: str) -> str:
    """获取批次输出路径"""
    return str(Path(base_path) / run_id)


def get_kg_data_output_path(base_path: str, run_id: str) -> str:
    """获取KG数据输出路径"""
    return str(Path(base_path) / run_id / "kg_data")

def get_incremental_output_path(base_path: str, run_id: str) -> str:
    """获取增量问题输出路径"""
    return str(Path(base_path) / run_id / "questions")


# ============================================================
# 批处理输出函数（处理爬取文档）
# ============================================================


def save_batch_output(
    batch_documents: List[CrawledDocumentState],
    batch_entities: List[KGEntity],
    batch_relations: List[KGRelation],
    batch_triples: List[KGTriple],
    output_path: str,
    batch_id: int,
    brand_name: str = "",
) -> Dict:
    """
    增量保存一批处理后的数据到文件

    Args:
        batch_documents: 本批次的文档列表（CrawledDocumentState格式）
        batch_entities: 本批次的KG实体
        batch_relations: 本批次的KG关系
        batch_triples: 本批次的KG三元组
        output_path: 输出目录路径（已包含批次ID）
        batch_id: 批次序号
        brand_name: 品牌名称

    Returns:
        保存结果信息
    """
    if not batch_documents:
        return {
            "success": True,
            "saved_count": 0,
            "message": "No data to save"
        }

    # 创建输出目录
    Path(output_path).mkdir(parents=True, exist_ok=True)

    # 生成文件名（不再包含时间戳，因为目录已有批次ID）
    filename = f"batch_{batch_id:04d}.json"
    filepath = Path(output_path) / filename

    # 构建保存数据
    save_data = {
        "batch_id": batch_id,
        "brand_name": brand_name,
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "documents_count": len(batch_documents),
            "entities_count": len(batch_entities),
            "relations_count": len(batch_relations),
            "triples_count": len(batch_triples),
        },
        "documents": batch_documents,
        "kg_data": {
            "entities": batch_entities,
            "relations": batch_relations,
            "triples": batch_triples,
        },
    }

    # 写入文件
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        print(f"[INFO] Batch #{batch_id} saved: {len(batch_documents)} docs, {len(batch_entities)} entities")

        return {
            "success": True,
            "saved_count": len(batch_documents),
            "filepath": str(filepath),
            "batch_id": batch_id,
        }
    except Exception as e:
        print(f"[ERROR] Failed to save batch output: {str(e)}")
        return {
            "success": False,
            "saved_count": 0,
            "error": str(e),
        }


def load_batch_output(
    output_path: str,
    batch_id: Optional[int] = None,
) -> Dict:
    """
    加载指定批次的数据文件

    Args:
        output_path: 输出目录路径
        batch_id: 特定批次序号（可选，None表示加载所有）

    Returns:
        包含documents和kg_data的字典
    """
    path = Path(output_path)

    if not path.exists():
        return {
            "documents": [],
            "kg_entities": [],
            "kg_relations": [],
            "kg_triples": [],
        }

    # 查找批次文件
    if batch_id is not None:
        pattern = f"batch_{batch_id:04d}.json"
        files = list(path.glob(pattern))
    else:
        files = sorted(path.glob("batch_*.json"))

    all_documents = []
    all_entities = []
    all_relations = []
    all_triples = []

    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 加载文档
            documents = data.get("documents", [])
            all_documents.extend(documents)

            # 加载KG数据
            kg_data = data.get("kg_data", {})
            all_entities.extend(kg_data.get("entities", []))
            all_relations.extend(kg_data.get("relations", []))
            all_triples.extend(kg_data.get("triples", []))

        except Exception as e:
            print(f"[WARN] Failed to load {filepath}: {str(e)}")

    return {
        "documents": all_documents,
        "kg_entities": all_entities,
        "kg_relations": all_relations,
        "kg_triples": all_triples,
    }


def get_batch_files_list(output_path: str) -> List[Dict]:
    """
    获取所有批次文件列表（用于VectorIndexAgent逐批读取）

    Args:
        output_path: 输出目录路径

    Returns:
        批次文件信息列表 [{"filepath": str, "batch_id": int, "documents_count": int}, ...]
    """
    path = Path(output_path)

    if not path.exists():
        return []

    files = sorted(path.glob("batch_*.json"))

    batch_info_list = []
    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            batch_info_list.append({
                "filepath": str(filepath),
                "batch_id": data.get("batch_id", 0),
                "documents_count": data.get("statistics", {}).get("documents_count", 0),
                "brand_name": data.get("brand_name", ""),
            })
        except Exception as e:
            print(f"[WARN] Failed to read batch file info {filepath}: {str(e)}")

    return batch_info_list


def merge_batch_statistics(output_path: str) -> Dict:
    """
    合并所有批次的统计信息

    Args:
        output_path: 输出目录路径

    Returns:
        合并后的统计信息
    """
    path = Path(output_path)

    if not path.exists():
        return {
            "total_documents": 0,
            "total_entities": 0,
            "total_relations": 0,
            "total_triples": 0,
            "batch_count": 0,
        }

    files = list(path.glob("batch_*.json"))

    total_documents = 0
    total_entities = 0
    total_relations = 0
    total_triples = 0

    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            stats = data.get("statistics", {})
            total_documents += stats.get("documents_count", 0)
            total_entities += stats.get("entities_count", 0)
            total_relations += stats.get("relations_count", 0)
            total_triples += stats.get("triples_count", 0)

        except Exception:
            pass

    return {
        "total_documents": total_documents,
        "total_entities": total_entities,
        "total_relations": total_relations,
        "total_triples": total_triples,
        "batch_count": len(files),
    }


# ============================================================
# 增量输出函数（处理问题对）
# ============================================================

def save_incremental_output(
    question_pairs: List[Dict],
    output_path: str,
    block_index: int,
    brand_name: str = "",
    save_id: int = 0,
) -> Dict:
    """
    增量保存问题对到文件

    Args:
        question_pairs: 要保存的问题对列表
        output_path: 输出目录路径（已包含批次ID）
        block_index: 当前处理的块索引
        brand_name: 品牌名称
        save_id: 保存序号

    Returns:
        保存结果信息
    """
    if not question_pairs:
        return {
            "success": True,
            "saved_count": 0,
            "message": "No data to save"
        }

    Path(output_path).mkdir(parents=True, exist_ok=True)

    # 文件名不再包含时间戳（目录已有批次ID）
    filename = f"questions_{save_id:04d}_block_{block_index:05d}.json"
    filepath = Path(output_path) / filename

    save_data = {
        "save_id": save_id,
        "block_index": block_index,
        "brand_name": brand_name,
        "timestamp": datetime.now().isoformat(),
        "question_count": len(question_pairs),
        "question_pairs": question_pairs,
    }

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        print(f"[INFO] Questions save #{save_id}: {len(question_pairs)} questions")

        return {
            "success": True,
            "saved_count": len(question_pairs),
            "filepath": str(filepath),
            "save_id": save_id,
        }
    except Exception as e:
        print(f"[ERROR] Failed to save incremental output: {str(e)}")
        return {
            "success": False,
            "saved_count": 0,
            "error": str(e),
        }


def load_incremental_output(
    output_path: str,
    save_id: Optional[int] = None,
) -> List[Dict]:
    """
    加载增量输出文件

    Args:
        output_path: 输出目录路径
        save_id: 特定保存序号（可选，None表示加载所有）

    Returns:
        问题对列表
    """
    path = Path(output_path)

    if not path.exists():
        return []

    if save_id is not None:
        pattern = f"questions_{save_id:04d}_*.json"
        files = list(path.glob(pattern))
    else:
        files = sorted(path.glob("questions_*.json"))

    all_question_pairs = []

    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            question_pairs = data.get("question_pairs", [])
            all_question_pairs.extend(question_pairs)

        except Exception as e:
            print(f"[WARN] Failed to load {filepath}: {str(e)}")

    return all_question_pairs


def merge_incremental_outputs(
    output_path: str,
    final_output_path: str,
    brand_name: str = "",
    competitors: List[str] = None,
) -> Dict:
    """
    合并所有增量输出为最终结果

    Args:
        output_path: 增量输出目录
        final_output_path: 最终输出文件路径
        brand_name: 品牌名称
        competitors: 竞品列表

    Returns:
        合并结果统计
    """
    all_question_pairs = load_incremental_output(output_path)

    if not all_question_pairs:
        print("[WARN] No incremental data found to merge")
        return {
            "success": False,
            "total_questions": 0,
            "message": "No incremental data found"
        }

    final_output = {
        "brand_name": brand_name,
        "competitors": competitors or [],
        "generated_at": datetime.now().isoformat(),
        "question_pairs": all_question_pairs,
        "statistics": {
            "total_questions": len(all_question_pairs),
            "total_rewritten_questions": sum(
                len(qp.get("rewritten_questions", []))
                for qp in all_question_pairs
            ),
        },
        "merge_info": {
            "incremental_files_count": len(list(Path(output_path).glob("questions_*.json"))),
            "merge_timestamp": datetime.now().isoformat(),
        }
    }

    Path(final_output_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(final_output_path, "w", encoding="utf-8") as f:
            json.dump(final_output, f, ensure_ascii=False, indent=2)

        print(f"[INFO] Merged {len(all_question_pairs)} questions to {final_output_path}")

        return {
            "success": True,
            "total_questions": len(all_question_pairs),
            "output_path": final_output_path,
        }
    except Exception as e:
        print(f"[ERROR] Failed to merge incremental outputs: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


def get_incremental_stats(output_path: str) -> Dict:
    """
    获取增量输出统计信息

    Args:
        output_path: 增量输出目录

    Returns:
        统计信息
    """
    path = Path(output_path)

    if not path.exists():
        return {
            "incremental_files_count": 0,
            "total_saved_questions": 0,
            "earliest_save": None,
            "latest_save": None,
        }

    files = sorted(path.glob("questions_*.json"))

    total_questions = 0
    earliest_timestamp = None
    latest_timestamp = None

    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            total_questions += data.get("question_count", 0)

            timestamp = data.get("timestamp")
            if timestamp:
                if earliest_timestamp is None:
                    earliest_timestamp = timestamp
                latest_timestamp = timestamp

        except Exception:
            pass

    return {
        "incremental_files_count": len(files),
        "total_saved_questions": total_questions,
        "earliest_save": earliest_timestamp,
        "latest_save": latest_timestamp,
    }


# ============================================================
# KG数据增量输出
# ============================================================

def save_kg_data_incremental(
    kg_entities: List[Dict],
    kg_relations: List[Dict],
    kg_triples: List[Dict],
    output_path: str,
    save_id: int = 0,
) -> Dict:
    """
    增量保存KG数据

    Args:
        kg_entities: KG实体列表
        kg_relations: KG关系列表
        kg_triples: KG三元组列表
        output_path: 输出目录路径（已包含批次ID）
        save_id: 保存序号

    Returns:
        保存结果信息
    """
    Path(output_path).mkdir(parents=True, exist_ok=True)

    # 文件名不再包含时间戳
    filename = f"kg_data_{save_id:04d}.json"
    filepath = Path(output_path) / filename

    save_data = {
        "save_id": save_id,
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "entities_count": len(kg_entities),
            "relations_count": len(kg_relations),
            "triples_count": len(kg_triples),
        },
        "entities": kg_entities,
        "relations": kg_relations,
        "triples": kg_triples,
    }

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        print(f"[INFO] KG data save #{save_id}: {len(kg_entities)} entities, {len(kg_relations)} relations")

        return {
            "success": True,
            "filepath": str(filepath),
            "entities_saved": len(kg_entities),
            "relations_saved": len(kg_relations),
            "triples_saved": len(kg_triples),
        }
    except Exception as e:
        print(f"[ERROR] Failed to save KG data: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


def load_kg_data_incremental(
    output_path: str,
    save_id: Optional[int] = None,
) -> Dict:
    """
    加载KG数据增量文件

    Args:
        output_path: 输出目录路径
        save_id: 特定保存序号（可选）

    Returns:
        KG数据字典
    """
    path = Path(output_path)

    if not path.exists():
        return {
            "entities": [],
            "relations": [],
            "triples": [],
        }

    if save_id is not None:
        pattern = f"kg_data_{save_id:04d}.json"
        files = list(path.glob(pattern))
    else:
        files = sorted(path.glob("kg_data_*.json"))

    all_entities = []
    all_relations = []
    all_triples = []

    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            all_entities.extend(data.get("entities", []))
            all_relations.extend(data.get("relations", []))
            all_triples.extend(data.get("triples", []))

        except Exception as e:
            print(f"[WARN] Failed to load {filepath}: {str(e)}")

    return {
        "entities": all_entities,
        "relations": all_relations,
        "triples": all_triples,
    }


# ============================================================
# 批次目录管理
# ============================================================

def list_all_runs(base_path: str) -> List[Dict]:
    """
    列出所有运行批次

    Args:
        base_path: 基础输出目录

    Returns:
        批次列表 [{"run_id": str, "timestamp": str, "stats": dict}, ...]
    """
    path = Path(base_path)

    if not path.exists():
        return []

    # 查找所有批次目录（格式：YYYYMMDD_HHMMSS）
    run_dirs = sorted([d for d in path.iterdir() if d.is_dir() and len(d.name) == 15 and "_" in d.name])

    runs = []
    for run_dir in run_dirs:
        run_id = run_dir.name

        # 获取批次统计
        batch_path = run_dir
        batch_files = list(run_dir.glob("batch_*.json"))

        # 获取问题统计
        questions_path = run_dir / "questions"
        question_files = list(questions_path.glob("questions_*.json")) if questions_path.exists() else []

        # 获取KG数据统计
        kg_path = run_dir / "kg_data"
        kg_files = list(kg_path.glob("kg_data_*.json")) if kg_path.exists() else []

        runs.append({
            "run_id": run_id,
            "path": str(run_dir),
            "batch_files_count": len(batch_files),
            "question_files_count": len(question_files),
            "kg_files_count": len(kg_files),
        })

    return runs


def get_latest_run(base_path: str) -> Optional[str]:
    """获取最近一次运行的批次ID"""
    runs = list_all_runs(base_path)
    if runs:
        return runs[-1]["run_id"]
    return None