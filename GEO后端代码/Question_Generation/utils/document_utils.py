"""
文档处理工具

统一处理文档清洗、分块、转换、元数据构建等操作：

包含：
1. TextCleaner: 文本清洗（非法字符、乱码、空行）
2. SemanticTextSplitter: 语义文本分块（支持重叠）
3. 文档处理函数: clean_and_split_documents, extract_kg_from_documents等

使用示例：
    from utils.document_utils import (
        TextCleaner,
        SemanticTextSplitter,
        clean_and_split_documents,
        extract_kg_from_documents,
        convert_to_document_states,
        build_document_metadata,
    )
"""

import re
from typing import List, Dict, Any, Optional
from core.state import CrawledDocumentState, TextBlock
from config.settings import settings


# ============================================================
# 文本清洗类
# ============================================================

class TextCleaner:
    """
    文本清洗器

    功能：
    1. 确保UTF-8编码
    2. 移除非法字符
    3. 移除空行
    4. 规范化空白字符
    """

    def __init__(self):
        self.illegal_chars_pattern = re.compile(
            r'[^一-龥a-zA-Z0-9\s\.,;:!?\'\"()（）、，。；：！？""\-—\n\t]'
        )

    def clean(self, text: str) -> str:
        """
        清洗文本

        Args:
            text: 输入文本

        Returns:
            清洗后的文本
        """
        text = self._ensure_utf8(text)
        text = self._remove_illegal_chars(text)
        text = self._remove_empty_lines(text)
        text = self._normalize_whitespace(text)
        return text.strip()

    def _ensure_utf8(self, text: str) -> str:
        """确保UTF-8编码"""
        try:
            if isinstance(text, bytes):
                text = text.decode('utf-8', errors='replace')
            return text
        except Exception:
            return str(text)

    def _remove_illegal_chars(self, text: str) -> str:
        """移除非法字符"""
        return self.illegal_chars_pattern.sub('', text)

    def _remove_empty_lines(self, text: str) -> str:
        """移除空行"""
        lines = text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        return '\n'.join(non_empty_lines)

    def _normalize_whitespace(self, text: str) -> str:
        """规范化空白字符"""
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text


# ============================================================
# 语义文本分块类
# ============================================================

class SemanticTextSplitter:
    """
    语义文本分块器

    功能：
    1. 按段落分割文本
    2. 支持分块重叠，确保语义完整性
    3. 返回TextBlock格式的分块列表
    """

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    def split(self, text: str) -> List[TextBlock]:
        """
        分块文本

        Args:
            text: 输入文本

        Returns:
            分块后的文本块列表（TextBlock格式）
        """
        paragraphs = self._split_by_paragraph(text)
        blocks = self._create_blocks_with_overlap(paragraphs)
        return blocks

    def _split_by_paragraph(self, text: str) -> List[str]:
        """按段落分割文本"""
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        if len(paragraphs) == 1:
            paragraphs = text.split('\n')
            paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs

    def _create_blocks_with_overlap(self, paragraphs: List[str]) -> List[TextBlock]:
        """创建带重叠的分块"""
        blocks = []
        current_content = ""
        block_id = 0
        overlap_buffer = ""

        for paragraph in paragraphs:
            if len(current_content) + len(paragraph) <= self.chunk_size:
                current_content += paragraph + "\n\n"
            else:
                if current_content:
                    final_content = overlap_buffer + current_content
                    blocks.append(self._create_block(block_id, final_content.strip()))
                    block_id += 1

                    overlap_buffer = self._get_overlap_content(current_content)

                current_content = overlap_buffer + paragraph + "\n\n"

        if current_content:
            blocks.append(self._create_block(block_id, current_content.strip()))

        return blocks

    def _get_overlap_content(self, content: str) -> str:
        """获取用于下一块重叠的内容"""
        if self.chunk_overlap <= 0 or len(content) <= self.chunk_overlap:
            return ""

        overlap_text = content[-self.chunk_overlap:]

        last_para_end = overlap_text.find('\n\n')
        if last_para_end > 0:
            overlap_text = overlap_text[last_para_end + 2:]

        return overlap_text.strip() + "\n\n" if overlap_text.strip() else ""

    def _create_block(self, block_id: int, content: str) -> TextBlock:
        """创建单个文本块"""
        return TextBlock(
            id=f"block_{block_id:03d}",
            content=content.strip(),
            original_content=" ".join(content.strip().split()),
            metadata=None,
        )


# ============================================================
# 文档处理函数
# ============================================================

def clean_and_split_documents(
    documents: List[Dict],
    text_cleaner: TextCleaner = None,
    text_splitter: SemanticTextSplitter = None,
    quality_threshold: float = 0.0,
    min_content_length: int = 50,
    filter_quality: bool = True,
) -> List[Dict]:
    """
    对文档进行清洗和分块（统一处理）

    质量过滤逻辑已迁移到EvaluationAgent

    Args:
        documents: 原始文档列表
        text_cleaner: 文本清洗器实例（可选，默认新建）
        text_splitter: 文本分块器实例（可选，默认新建）
        quality_threshold: 质量阈值（低于此值的文档会被过滤）
        min_content_length: 最小内容长度（清洗后过短会被过滤）
        filter_quality: 是否进行质量过滤

    Returns:
        分块后的文档列表
    """
    # 使用默认实例
    if text_cleaner is None:
        text_cleaner = TextCleaner()
    if text_splitter is None:
        text_splitter = SemanticTextSplitter()

    # 使用EvaluationAgent进行内容质量评估与过滤
    if filter_quality:
        from agents import get_evaluation_agent  # 延迟导入，避免循环依赖
        eval_agent = get_evaluation_agent()
        eval_result = eval_agent.evaluate_crawler_content(
            documents=documents,
            quality_threshold=quality_threshold,
            min_content_length=min_content_length,
        )
        filtered_documents = eval_result["filtered_documents"]
        print(f"[INFO] Content evaluation: {eval_result['filtered_count']} filtered, {eval_result['retained_count']} retained")
    else:
        filtered_documents = documents

    # 对过滤后的文档进行分块
    total_filtered = len(filtered_documents)
    print(f"[INFO] 分块处理: 共{total_filtered}个文档")
    split_docs = []
    for idx, doc in enumerate(filtered_documents, 1):
        doc_id = doc.get("doc_id", "")
        title = doc.get("title", "")
        cleaned_content = doc.get("cleaned_content", doc.get("content", ""))

        if not cleaned_content:
            continue

        # 分块
        text_blocks = text_splitter.split(cleaned_content)

        # 为每个分块创建文档（保留原始元数据）
        for i, block in enumerate(text_blocks):
            split_doc = {
                "doc_id": f"{doc_id}_block_{i:03d}",
                "parent_doc_id": doc_id,
                "title": f"{title} - 分块{i+1}",
                "content": block["content"],
                "source_type": doc.get("source_type", ""),
                "source_url": doc.get("source_url", ""),
                "source_date": doc.get("source_date") or 0,
                "crawl_timestamp": doc.get("crawl_timestamp") or 0,
                "keywords": doc.get("keywords", []),
                "category": doc.get("category", ""),
                "brand_name": doc.get("brand_name", ""),
                "quality_score": doc.get("quality_score", 0.0),
                "block_index": i,
                "total_blocks": len(text_blocks),
            }
            split_docs.append(split_doc)
        
        # 进度打印
        if idx % 5 == 0 or idx == total_filtered:
            print(f"  分块进度: {idx}/{total_filtered} (累计{len(split_docs)}块)")

    print(f"[INFO] 分块完成: 共{len(split_docs)}个文本块")
    return split_docs


def extract_kg_from_documents(
    split_documents: List[Dict],
    kg_builder,
    use_llm: bool = True,
) -> List[Dict]:
    """
    对文档进行KG抽取（统一处理）

    Args:
        split_documents: 分块后的文档列表
        kg_builder: KG构建器实例
        use_llm: 是否使用LLM精细化

    Returns:
        KG文档列表
    """
    docs_for_kg = [
        {
            "doc_id": doc["doc_id"],
            "content": doc["content"],
        }
        for doc in split_documents
    ]

    kg_data = kg_builder.build_from_documents(docs_for_kg, use_llm=use_llm)

    return kg_data.get("documents", [])


def convert_to_document_states(
    split_documents: List[Dict],
    kg_documents: List[Dict],
) -> List[CrawledDocumentState]:
    """
    将文档转换为CrawledDocumentState格式（统一处理）

    Args:
        split_documents: 分块后的文档列表
        kg_documents: KG抽取结果列表

    Returns:
        CrawledDocumentState列表
    """
    kg_map = {kg["doc_id"]: kg for kg in kg_documents}

    states = []
    for doc in split_documents:
        doc_id = doc["doc_id"]
        kg_doc = kg_map.get(doc_id, {})

        state = CrawledDocumentState(
            doc_id=doc_id,
            title=doc.get("title", ""),
            content=doc.get("content", ""),
            source_type=doc.get("source_type", ""),
            source_url=doc.get("source_url", ""),
            source_date=doc.get("source_date") or 0,
            crawl_timestamp=doc.get("crawl_timestamp") or 0,
            keywords=doc.get("keywords", []),
            category=doc.get("category", ""),
            brand_name=doc.get("brand_name", ""),
            quality_score=doc.get("quality_score", 0.0),
            entities=kg_doc.get("entities", []),
            relations=kg_doc.get("relations", []),
            indexed=False,
        )
        states.append(state)

    return states


def build_document_metadata(doc: Dict) -> Dict[str, Any]:
    """
    构建文档元数据（用于向量索引）

    Args:
        doc: 文档字典（CrawledDocumentState格式）

    Returns:
        元数据字典（包含所有Schema字段，GEO字段使用默认值）
    """
    entity_tags = [
        e.get("entity_name", "") for e in doc.get("entities", [])
        if e.get("entity_name")
    ]

    relation_types = [
        r.get("relation_type", "") for r in doc.get("relations", [])
        if r.get("relation_type")
    ]

    entity_confidences = [
        e.get("confidence", 0) for e in doc.get("entities", [])
    ]
    kg_confidence = (
        sum(entity_confidences) / len(entity_confidences)
        if entity_confidences else 0.0
    )

    metadata = {
        # 基础元数据字段
        "source_type": doc.get("source_type", ""),
        "source_url": doc.get("source_url", ""),
        "source_title": doc.get("title", ""),
        "source_date": doc.get("source_date") or 0,
        "entity_tags": entity_tags,
        "relation_types": relation_types,
        "kg_confidence": round(kg_confidence, 2),
        "category": doc.get("category", ""),
        "keywords": doc.get("keywords", []),
        "quality_score": doc.get("quality_score", 0.0),
        "crawl_timestamp": doc.get("crawl_timestamp") or 0,
        "brand_name": doc.get("brand_name", ""),
        "doc_id": doc.get("doc_id", ""),
        # GEO字段默认值（GEO分析后才会填充）
        "generated_questions": "",
        "question_count": 0,
        "geo_analysis_status": "pending",
        "geo_total_analyses": 0,
        "geo_deepseek_mentioned_count": 0,
        "geo_deepseek_avg_rank": 0.0,
        "geo_deepseek_avg_sentiment": 0.0,
        "geo_deepseek_authority_avg": 0.0,
        "geo_qwen_mentioned_count": 0,
        "geo_qwen_avg_rank": 0.0,
        "geo_qwen_avg_sentiment": 0.0,
        "geo_qwen_authority_avg": 0.0,
        "geo_kimi_mentioned_count": 0,
        "geo_kimi_avg_rank": 0.0,
        "geo_kimi_avg_sentiment": 0.0,
        "geo_kimi_authority_avg": 0.0,
        "geo_doubao_mentioned_count": 0,
        "geo_doubao_avg_rank": 0.0,
        "geo_doubao_avg_sentiment": 0.0,
        "geo_doubao_authority_avg": 0.0,
        "geo_yuanbao_mentioned_count": 0,
        "geo_yuanbao_avg_rank": 0.0,
        "geo_yuanbao_avg_sentiment": 0.0,
        "geo_yuanbao_authority_avg": 0.0,
        "geo_competitor_summary": "",
        "geo_analysis_timestamp": 0,
    }

    return metadata


def batch_insert_with_fallback(
    items: List[Any],
    batch_insert_func,
    single_insert_func,
    batch_size: int = 100,
) -> tuple:
    """
    批量插入带逐条失败重试（统一处理）

    Args:
        items: 待插入的项目列表
        batch_insert_func: 批量插入函数
        single_insert_func: 单条插入函数
        batch_size: 批量大小

    Returns:
        (success_count, failed_count)
    """
    success_count = 0
    failed_count = 0

    try:
        success = batch_insert_func(items)
        if success:
            success_count = len(items)
        else:
            for item in items:
                try:
                    single_insert_func(item)
                    success_count += 1
                except Exception:
                    failed_count += 1
    except Exception as e:
        failed_count = len(items)
        print(f"[ERROR] Batch insert failed: {str(e)}")

    return success_count, failed_count


def extract_keywords_from_text(text: str, min_length: int = 2) -> List[str]:
    """
    从文本中提取中文关键词（统一处理）

    Args:
        text: 输入文本
        min_length: 最小关键词长度

    Returns:
        关键词列表
    """
    pattern = re.compile(r'[一-龥]{2,}')
    keywords = pattern.findall(text)

    return keywords[:10] if len(keywords) > 10 else keywords