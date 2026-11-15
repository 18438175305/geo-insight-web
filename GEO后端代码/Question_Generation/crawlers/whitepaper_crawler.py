"""
白皮书/PDF爬虫

解析企业白皮书、产品说明书等PDF文档
"""

import os
import re
import hashlib
from typing import List, Dict, Optional
from .base_crawler import BaseCrawler, CrawledDocument


class PDFParser:
    """PDF解析器，支持pdfplumber和PyMuPDF两种方式"""

    def __init__(self, method: str = "pdfplumber"):
        self.method = method

    def parse(self, pdf_path: str) -> List[str]:
        """解析PDF文件，返回每页内容列表"""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if self.method == "pdfplumber":
            return self._parse_with_pdfplumber(pdf_path)
        elif self.method == "pymupdf":
            return self._parse_with_pymupdf(pdf_path)
        else:
            return self._parse_with_pdfplumber(pdf_path)

    def _parse_with_pdfplumber(self, pdf_path: str) -> List[str]:
        try:
            import pdfplumber
        except ImportError:
            print("[WARN] pdfplumber not installed, trying pymupdf")
            return self._parse_with_pymupdf(pdf_path)

        pages_content = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text = self._clean_text(text)
                    pages_content.append(text)
        return pages_content

    def _parse_with_pymupdf(self, pdf_path: str) -> List[str]:
        try:
            import fitz
        except ImportError:
            raise ImportError("Please install pdfplumber or pymupdf")

        pages_content = []
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text:
                text = self._clean_text(text)
                pages_content.append(text)
        doc.close()
        return pages_content

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        return text.strip()


class WhitepaperCrawler(BaseCrawler):
    """
    白皮书/PDF爬虫

    解析企业白皮书、产品说明书等PDF文档
    """

    def __init__(self, brand_name: str):
        super().__init__(brand_name)
        self.pdf_parser = PDFParser()

    def get_source_type(self) -> str:
        return "whitepaper"

    def crawl(self, config: Dict) -> List[CrawledDocument]:
        """
        解析PDF文档

        Config格式:
        {
            "enabled": true,
            "pdf_files": [
                {
                    "path": "data/whitepapers/yunnan_baiyao_product.pdf",
                    "title": "产品说明书",
                    "category": "产品说明书"
                },
                {
                    "path": "data/whitepapers/yunnan_baiyao_history.pdf",
                    "title": "品牌历史",
                    "category": "品牌历史"
                },
            ],
            "chunk_size": 500,
            "extract_images": False,
        }

        Args:
            config: 爬取配置

        Returns:
            爬取文档列表
        """
        documents = []
        pdf_files = config.get("pdf_files", [])
        chunk_size = config.get("chunk_size", 500)

        for pdf_config in pdf_files:
            pdf_path = pdf_config.get("path", "")
            if not pdf_path:
                continue

            if not os.path.exists(pdf_path):
                print(f"[WARN] PDF file not found: {pdf_path}")
                continue

            try:
                docs = self._parse_pdf(pdf_path, pdf_config, chunk_size)
                documents.extend(docs)
                print(f"[INFO] Parsed PDF: {pdf_path} ({len(docs)} pages)")
            except Exception as e:
                print(f"[ERROR] Failed to parse PDF {pdf_path}: {str(e)}")

        return documents

    def _parse_pdf(
        self,
        pdf_path: str,
        pdf_config: Dict,
        chunk_size: int = 500
    ) -> List[CrawledDocument]:
        """
        解析PDF文件

        Args:
            pdf_path: PDF文件路径
            pdf_config: PDF配置
            chunk_size: 分块大小

        Returns:
            文档列表
        """
        content_pages = self.pdf_parser.parse(pdf_path)

        documents = []
        for i, page_content in enumerate(content_pages):
            if not page_content.strip():
                continue

            # 如果内容过长，进行分块
            if len(page_content) > chunk_size:
                chunks = self._split_content(page_content, chunk_size)
                for j, chunk in enumerate(chunks):
                    doc = self._create_doc_from_chunk(
                        chunk, pdf_path, pdf_config, i, j
                    )
                    if doc:
                        documents.append(doc)
            else:
                doc = self._create_doc_from_page(
                    page_content, pdf_path, pdf_config, i
                )
                if doc:
                    documents.append(doc)

        return documents

    def _split_content(self, content: str, chunk_size: int) -> List[str]:
        """
        分割内容

        Args:
            content: 内容文本
            chunk_size: 分块大小

        Returns:
            分块列表
        """
        chunks = []
        paragraphs = content.split('\n\n')

        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += "\n\n" + para

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _create_doc_from_page(
        self,
        content: str,
        pdf_path: str,
        pdf_config: Dict,
        page_num: int
    ) -> Optional[CrawledDocument]:
        """
        从页面内容创建文档

        Args:
            content: 页面内容
            pdf_path: PDF路径
            pdf_config: PDF配置
            page_num: 页码

        Returns:
            文档或None
        """
        if len(content) < 50:
            return None

        title = pdf_config.get("title", os.path.basename(pdf_path))
        category = pdf_config.get("category", "白皮书")

        doc_id = f"{self.get_source_type()}_{hashlib.md5(f'{pdf_path}_page_{page_num}'.encode()).hexdigest()[:12]}"

        return CrawledDocument(
            doc_id=doc_id,
            title=f"{title} - 第{page_num + 1}页",
            content=content,
            source_type=self.get_source_type(),
            source_url=pdf_path,
            source_date=None,
            crawl_timestamp=self.crawl_timestamp,
            keywords=self.extract_keywords(content),
            category=category,
            brand_name=self.brand_name,
            quality_score=self.calculate_quality_score(content),
        )

    def _create_doc_from_chunk(
        self,
        content: str,
        pdf_path: str,
        pdf_config: Dict,
        page_num: int,
        chunk_num: int
    ) -> Optional[CrawledDocument]:
        """
        从分块内容创建文档

        Args:
            content: 分块内容
            pdf_path: PDF路径
            pdf_config: PDF配置
            page_num: 页码
            chunk_num: 分块号

        Returns:
            文档或None
        """
        if len(content) < 50:
            return None

        title = pdf_config.get("title", os.path.basename(pdf_path))
        category = pdf_config.get("category", "白皮书")

        doc_id = f"{self.get_source_type()}_{hashlib.md5(f'{pdf_path}_page_{page_num}_chunk_{chunk_num}'.encode()).hexdigest()[:12]}"

        return CrawledDocument(
            doc_id=doc_id,
            title=f"{title} - 第{page_num + 1}页-片段{chunk_num + 1}",
            content=content,
            source_type=self.get_source_type(),
            source_url=pdf_path,
            source_date=None,
            crawl_timestamp=self.crawl_timestamp,
            keywords=self.extract_keywords(content),
            category=category,
            brand_name=self.brand_name,
            quality_score=self.calculate_quality_score(content),
        )

    def extract_keywords(self, content: str) -> List[str]:
        """提取白皮书关键词"""
        keywords = [self.brand_name]

        # 白皮书通常包含专业术语
        import re
        terms = re.findall(r'[一-龥]{2,8}', content)

        # 计算词频
        word_freq = {}
        for term in terms:
            word_freq[term] = word_freq.get(term, 0) + 1

        # 取前15个高频词
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:15]
        keywords.extend([w[0] for w in top_words])

        return keywords