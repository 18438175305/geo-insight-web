"""
系统配置管理,各模块使用独立的本地模型：- kg_extraction: KG知识提取模型 - question_generation: 问题生成模型
- question_rewrite: 问题改写模型 - question_evaluation: 问题评估模型 - embedding: Embedding向量模型
"""
import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv() # 从 .env 文件加载环境变量到 Python 进程中

class ModelConfig(BaseModel):
    """单个模型配置"""
    model_path: str          # 本地模型文件路径
    temperature: float = 0.7  # 生成随机性：0=确定性输出，1=高度随机，越高越多样化
    max_tokens: int = 2048    # 最大输出长度（token数），超过会截断

class KGExtractionConfig(BaseModel):
    """KG知识提取模型配置"""
    model: ModelConfig = ModelConfig(model_path="models/kg_extraction", max_tokens=2048)  # KG提取专用模型，输出较短
    min_confidence: float = 0.6    # 置信度阈值
    use_ner_preprocess: bool = True  # 是否使用规则预处理（NER）提供候选
    use_llm_refinement: bool = True  # 是否使用LLM精细化抽取结果
    timeout: int = 60  # LLM调用超时时间（秒）

class QuestionGenerationConfig(BaseModel):
    """问题生成模型配置"""
    model: ModelConfig = ModelConfig(model_path="models/question_generation",temperature=0.8, max_tokens=1024) # 较高temperature增加问题多样性; 生成3-5个问题，中等长度足够

class QuestionRewriteConfig(BaseModel):
    """问题改写模型配置"""
    model: ModelConfig = ModelConfig(model_path="models/question_rewrite", temperature=0.7, max_tokens=1024) # 改写5-8个版本，中等长度

class QuestionEvaluationConfig(BaseModel):
    """问题评估模型配置"""
    model: ModelConfig = ModelConfig(model_path="models/question_evaluation", temperature=0.3, max_tokens=2048) # 低temperature保证评估结果稳定一致; 只输出评分和简短理由，短长度足够
    brand_leak_threshold: float = 0.0    # 品牌泄露阈值：0表示不允许任何泄露
    min_entity_coverage: float = 0.1      # 最低实体覆盖率，过低表示问题与KG关联不足
    min_objective_score: float = 60       # 最低客观得分阈值，低于此值的问题被过滤
    min_subjective_score: float = 60      # 最低主观得分阈值，低于此值的问题被过滤
    min_total_score: float = 60           # 最低综合得分阈值（主观评估后），低于此值的问题对被过滤
    subjective_batch_size: int = 5        # 主观评估批次大小，每批评估的问题数量

class EmbeddingConfig(BaseModel):
    """Embedding向量模型配置"""
    model_path: str = "models/embedding"  # Embedding模型文件路径

class MilvusConfig(BaseModel):
    """Milvus向量数据库配置"""
    host: str = "localhost"      # Milvus服务器地址
    port: str = "19530"          # Milvus服务器端口
    embedding_dim: int = 1024    # 向量维度，需与Embedding模型输出维度一致

class CrawlerConfig(BaseModel):
    """爬虫配置"""
    timeout: int = 30                      # 单次请求超时时间（秒）
    retry_count: int = 3                   # 请求失败重试次数
    delay_range: tuple[int, int] = (1, 3)  # 请求间隔范围（秒），避免高频请求被封
    cache_enabled: bool = True             # 是否启用本地缓存
    cache_path: str = "data/crawled_cache" # 缓存文件保存路径
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"  # 浏览器标识，模拟正常访问
    batch_size: int = 50                   # 批处理大小：每批处理的文档数量
    batch_output_path: str = "data/batch_output"  # 批处理增量输出路径

class GEOTrackingConfig(BaseModel):
    """GEO追踪分析配置"""
    enabled: bool = False                  # 是否启用GEO分析
    platforms: list[str] = ["deepseek", "qwen", "kimi", "doubao", "yuanbao"]  # 分析平台列表
    timeout: int = 60                      # 单次API调用超时时间（秒）
    retry_count: int = 3                   # API调用失败重试次数
    delay_range: tuple[int, int] = (2, 5)  # API调用间隔范围（秒）
    overwrite_geo: bool = True             # 是否覆盖已存在的GEO分析记录（True=覆盖，False=跳过重复）
    # API Keys（从环境变量加载）
    deepseek_api_key: str = ""
    qwen_api_key: str = ""
    kimi_api_key: str = ""
    doubao_api_key: str = ""
    yuanbao_api_key: str = ""

class GEOAnalysisConfig(BaseModel):
    """GEO分析LLM模型配置（用于精确提取各项指标）"""
    model: ModelConfig = ModelConfig(
        model_path="models/geo_analysis",
        temperature=0.1,  # 低temperature保证分析结果稳定一致
        max_tokens=2048   # 分析结果可能较长
    )
    prompt_path: str = "data/prompts/geo_analysis_prompt.md"  # 分析Prompt文件路径
    use_llm_analysis: bool = True  # 是否使用LLM进行分析（替代正则方案）
    fallback_to_regex: bool = True  # LLM失败时是否回退到正则方案

class Settings(BaseModel):
    """系统配置"""
    kg_extraction: KGExtractionConfig = KGExtractionConfig()
    question_generation: QuestionGenerationConfig = QuestionGenerationConfig()
    question_rewrite: QuestionRewriteConfig = QuestionRewriteConfig()
    question_evaluation: QuestionEvaluationConfig = QuestionEvaluationConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    milvus: MilvusConfig = MilvusConfig()
    crawler: CrawlerConfig = CrawlerConfig()
    geo_tracking: GEOTrackingConfig = GEOTrackingConfig()
    geo_analysis: GEOAnalysisConfig = GEOAnalysisConfig()  # GEO分析LLM配置

    chunk_size: int = 500
    chunk_overlap: int = 50
    max_retry_count: int = 3

    def __init__(self, **data):
        super().__init__(**data)
        self._load_from_env()

    def _load_from_env(self):
        """从环境变量加载配置（覆盖默认值）"""
        # KG提取模型
        kg_updates = {}
        if os.getenv("KG_MODEL_PATH"):
            kg_updates["model"] = ModelConfig(
                model_path=os.getenv("KG_MODEL_PATH"),
                temperature=float(os.getenv("KG_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("KG_MAX_TOKENS", "2048")),
            )
        if os.getenv("KG_MIN_CONFIDENCE"):
            kg_updates["min_confidence"] = float(os.getenv("KG_MIN_CONFIDENCE"))
        if os.getenv("KG_USE_NER_PREPROCESS"):
            kg_updates["use_ner_preprocess"] = os.getenv("KG_USE_NER_PREPROCESS").lower() == "true"
        if os.getenv("KG_USE_LLM_REFINEMENT"):
            kg_updates["use_llm_refinement"] = os.getenv("KG_USE_LLM_REFINEMENT").lower() == "true"
        if os.getenv("KG_TIMEOUT"):
            kg_updates["timeout"] = int(os.getenv("KG_TIMEOUT"))
        if kg_updates:
            self.kg_extraction = KGExtractionConfig(**{**self.kg_extraction.model_dump(), **kg_updates})

        # 问题生成模型
        qg_updates = {}
        if os.getenv("QG_MODEL_PATH"):
            qg_updates["model"] = ModelConfig(
                model_path=os.getenv("QG_MODEL_PATH"),
                temperature=float(os.getenv("QG_TEMPERATURE", "0.8")),
                max_tokens=int(os.getenv("QG_MAX_TOKENS", "1024")),
            )
        if qg_updates:
            self.question_generation = QuestionGenerationConfig(**{**self.question_generation.model_dump(), **qg_updates})

        # 问题改写模型
        qr_updates = {}
        if os.getenv("QR_MODEL_PATH"):
            qr_updates["model"] = ModelConfig(
                model_path=os.getenv("QR_MODEL_PATH"),
                temperature=float(os.getenv("QR_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("QR_MAX_TOKENS", "1024")),
            )
        if qr_updates:
            self.question_rewrite = QuestionRewriteConfig(**{**self.question_rewrite.model_dump(), **qr_updates})

        # 问题评估模型
        qe_updates = {}
        if os.getenv("QE_MODEL_PATH"):
            qe_updates["model"] = ModelConfig(
                model_path=os.getenv("QE_MODEL_PATH"),
                temperature=float(os.getenv("QE_TEMPERATURE", "0.3")),
                max_tokens=int(os.getenv("QE_MAX_TOKENS", "512")),
            )
        if os.getenv("QE_BRAND_LEAK_THRESHOLD"):
            qe_updates["brand_leak_threshold"] = float(os.getenv("QE_BRAND_LEAK_THRESHOLD"))
        if os.getenv("QE_MIN_OBJECTIVE_SCORE"):
            qe_updates["min_objective_score"] = float(os.getenv("QE_MIN_OBJECTIVE_SCORE"))
        if os.getenv("QE_MIN_SUBJECTIVE_SCORE"):
            qe_updates["min_subjective_score"] = float(os.getenv("QE_MIN_SUBJECTIVE_SCORE"))
        if os.getenv("QE_MIN_ENTITY_COVERAGE"):
            qe_updates["min_entity_coverage"] = float(os.getenv("QE_MIN_ENTITY_COVERAGE"))
        if os.getenv("QE_MIN_TOTAL_SCORE"):
            qe_updates["min_total_score"] = float(os.getenv("QE_MIN_TOTAL_SCORE"))
        if os.getenv("QE_SUBJECTIVE_BATCH_SIZE"):
            qe_updates["subjective_batch_size"] = int(os.getenv("QE_SUBJECTIVE_BATCH_SIZE"))
        if qe_updates:
            self.question_evaluation = QuestionEvaluationConfig(**{**self.question_evaluation.model_dump(), **qe_updates})

        # Embedding模型
        if os.getenv("EMBEDDING_MODEL_PATH"):
            self.embedding = EmbeddingConfig(model_path=os.getenv("EMBEDDING_MODEL_PATH"))

        # Milvus配置
        milvus_updates = {}
        if os.getenv("MILVUS_HOST"):
            milvus_updates["host"] = os.getenv("MILVUS_HOST")
        if os.getenv("MILVUS_PORT"):
            milvus_updates["port"] = os.getenv("MILVUS_PORT")
        if os.getenv("MILVUS_EMBEDDING_DIM"):
            milvus_updates["embedding_dim"] = int(os.getenv("MILVUS_EMBEDDING_DIM"))
        if milvus_updates:
            self.milvus = MilvusConfig(**{**self.milvus.model_dump(), **milvus_updates})

        # 爬虫配置
        crawler_updates = {}
        if os.getenv("CRAWLER_TIMEOUT"):
            crawler_updates["timeout"] = int(os.getenv("CRAWLER_TIMEOUT"))
        if os.getenv("CRAWLER_RETRY_COUNT"):
            crawler_updates["retry_count"] = int(os.getenv("CRAWLER_RETRY_COUNT"))
        if os.getenv("CRAWLER_DELAY_MIN") and os.getenv("CRAWLER_DELAY_MAX"):
            crawler_updates["delay_range"] = (int(os.getenv("CRAWLER_DELAY_MIN")), int(os.getenv("CRAWLER_DELAY_MAX")))
        if os.getenv("CRAWLER_CACHE_ENABLED"):
            crawler_updates["cache_enabled"] = os.getenv("CRAWLER_CACHE_ENABLED").lower() == "true"
        if os.getenv("CRAWLER_CACHE_PATH"):
            crawler_updates["cache_path"] = os.getenv("CRAWLER_CACHE_PATH")
        if os.getenv("CRAWLER_USER_AGENT"):
            crawler_updates["user_agent"] = os.getenv("CRAWLER_USER_AGENT")
        if os.getenv("CRAWLER_BATCH_SIZE"):
            crawler_updates["batch_size"] = int(os.getenv("CRAWLER_BATCH_SIZE"))
        if os.getenv("CRAWLER_BATCH_OUTPUT_PATH"):
            crawler_updates["batch_output_path"] = os.getenv("CRAWLER_BATCH_OUTPUT_PATH")
        if crawler_updates:
            self.crawler = CrawlerConfig(**{**self.crawler.model_dump(), **crawler_updates})

        # 全局配置
        if os.getenv("CHUNK_SIZE"):
            self.chunk_size = int(os.getenv("CHUNK_SIZE"))
        if os.getenv("CHUNK_OVERLAP"):
            self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP"))
        if os.getenv("MAX_RETRY_COUNT"):
            self.max_retry_count = int(os.getenv("MAX_RETRY_COUNT"))

        # GEO追踪配置
        geo_updates = {}
        if os.getenv("GEO_ENABLED"):
            geo_updates["enabled"] = os.getenv("GEO_ENABLED").lower() == "true"
        if os.getenv("GEO_PLATFORMS"):
            geo_updates["platforms"] = os.getenv("GEO_PLATFORMS").split(",")
        if os.getenv("GEO_TIMEOUT"):
            geo_updates["timeout"] = int(os.getenv("GEO_TIMEOUT"))
        if os.getenv("GEO_RETRY_COUNT"):
            geo_updates["retry_count"] = int(os.getenv("GEO_RETRY_COUNT"))
        if os.getenv("GEO_OVERWRITE"):
            geo_updates["overwrite_geo"] = os.getenv("GEO_OVERWRITE").lower() == "true"
        # API Keys
        if os.getenv("DEEPSEEK_API_KEY"):
            geo_updates["deepseek_api_key"] = os.getenv("DEEPSEEK_API_KEY")
        if os.getenv("QWEN_API_KEY"):
            geo_updates["qwen_api_key"] = os.getenv("QWEN_API_KEY")
        if os.getenv("KIMI_API_KEY"):
            geo_updates["kimi_api_key"] = os.getenv("KIMI_API_KEY")
        if os.getenv("DOUBAO_API_KEY"):
            geo_updates["doubao_api_key"] = os.getenv("DOUBAO_API_KEY")
        if os.getenv("YUANBAO_API_KEY"):
            geo_updates["yuanbao_api_key"] = os.getenv("YUANBAO_API_KEY")
        if geo_updates:
            self.geo_tracking = GEOTrackingConfig(**{**self.geo_tracking.model_dump(), **geo_updates})

        # GEO分析LLM配置
        geo_analysis_updates = {}
        if os.getenv("GEO_ANALYSIS_MODEL_PATH"):
            geo_analysis_updates["model"] = ModelConfig(
                model_path=os.getenv("GEO_ANALYSIS_MODEL_PATH"),
                temperature=float(os.getenv("GEO_ANALYSIS_TEMPERATURE", "0.1")),
                max_tokens=int(os.getenv("GEO_ANALYSIS_MAX_TOKENS", "2048")),
            )
        if os.getenv("GEO_ANALYSIS_PROMPT_PATH"):
            geo_analysis_updates["prompt_path"] = os.getenv("GEO_ANALYSIS_PROMPT_PATH")
        if os.getenv("GEO_ANALYSIS_USE_LLM"):
            geo_analysis_updates["use_llm_analysis"] = os.getenv("GEO_ANALYSIS_USE_LLM").lower() == "true"
        if os.getenv("GEO_ANALYSIS_FALLBACK"):
            geo_analysis_updates["fallback_to_regex"] = os.getenv("GEO_ANALYSIS_FALLBACK").lower() == "true"
        if geo_analysis_updates:
            self.geo_analysis = GEOAnalysisConfig(**{**self.geo_analysis.model_dump(), **geo_analysis_updates})

    def get_external_collection_name(self, brand_name: str) -> str:
        """获取品牌对应的外部知识库Collection名称（动态生成，无硬编码）"""
        return f"external_kb_{brand_name}"

settings = Settings()