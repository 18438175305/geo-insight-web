> **开源范围说明**：因项目保密要求，核心提示词模板、奖励函数实现、KG抽取与各Agent核心代码、完整训练数据未随本仓库公开（可应评审要求线下演示）。本 README 描述系统完整设计；仓库保留架构配置、爬虫/平台接入、向量库封装、真实运行产物与训练产出摘要。

# 品牌推荐问题生成系统

基于知识图谱和LLM的品牌推荐问题生成系统，支持多源数据爬取、知识图谱抽取、向量索引、问题生成与评估、GEO追踪分析、以及问题生成模型微调（SFT/GRPO）。

---

## 目录

- [项目概述](#项目概述)
- [核心功能](#核心功能)
- [项目结构](#项目结构)
- [环境配置](#环境配置)
- [快速开始](#快速开始)
- [运行模式详解](#运行模式详解)
- [crawl模式完整流程](#crawl模式完整流程)
- [GEO追踪分析](#geo追踪分析)
- [模型说明](#模型说明)
- [输出格式](#输出格式)

---

## 项目概述

本系统面向品牌推荐场景，通过爬取多源数据（官网、知乎、小红书、白皮书等），构建品牌知识图谱，并基于知识图谱自动生成高质量的品牌推荐相关问题。生成的数据可用于：

- 品牌问答系统训练
- 推荐系统评估
- GEO（Generative Engine Optimization）品牌可见性分析
- **问题生成模型微调（SFT/GRPO）**

---

## 核心功能

| 功能模块 | 描述 |
|---------|------|
| **多源爬取** | 支持官方网站、知乎、小红书、白皮书等多种数据源 |
| **知识图谱抽取** | 自动抽取实体（产品、功效、成分等）和关系，构建KG |
| **向量索引** | 使用 Milvus 构建向量索引，支持语义检索 |
| **问题生成** | 基于KG实体和品牌信息，生成推荐相关问题（核心功能） |
| **质量评估** | 双重评估机制：客观指标 + LLM主观评估 |
| **问题改写** | 对主问题进行多样化改写，生成问题对 |
| **GEO追踪分析** | 调用5大AI平台分析品牌可见性，使用微调模型进行情感分析和建议生成 |
| **模型微调** | 支持 SFT（监督微调）和 GRPO（强化学习优化）训练问题生成模型 |

---

## 项目结构

```
Question_Generation/
├── main.py                      # 主入口（6种运行模式）
│
├── core/                        # 核心模块
│   ├── graph.py                 # LangGraph工作流定义
│   └── state.py                 # 状态数据结构（GraphState + AIResponse）
│
├── agents/                      # Agent模块（工作流节点）
│   ├── base_agent.py            # Agent基类
│   ├── data_processing_agent.py # 数据处理Agent（爬取+清洗+KG+批处理）
│   ├── vector_index_agent.py    # 向量索引Agent
│   ├── question_generation_agent.py # 问题生成Agent
│   ├── question_rewrite_agent.py    # 问题改写Agent
│   ├── evaluation_agent.py          # 评估Agent
│   ├── kb_management_agent.py       # 知识库管理Agent
│   └── geo_tracking_agent.py        # GEO追踪Agent（完整复制GEO_Tracker功能）
│
├── crawlers/                    # 爬虫模块
│   ├── base_crawler.py          # 爬虫基类
│   ├── crawler_manager.py       # 爬虫管理器
│   ├── official_site_crawler.py # 官网爬虫
│   ├── zhihu_crawler.py         # 知乎爬虫
│   ├── xiaohongshu_crawler.py   # 小红书爬虫
│   └── whitepaper_crawler.py    # 白皮书爬虫
│
├── kg_extraction/               # 知识图谱抽取
│   ├── kg_schema.py             # KG Schema定义
│   └── kg_builder.py            # KG构建器（NER+LLM）
│
├── vectorstore/                 # 向量存储
│   ├── milvus_client.py         # Milvus客户端
│   ├── milvus_schema.py         # Milvus Schema（含GEO汇总字段）
│   ├── embedding.py             # Embedding模型
│   ├── geo_analysis_schema.py   # GEO分析Schema
│   └── geo_analysis_client.py   # GEO分析Milvus客户端
│
├── models/                      # 本地模型
│   ├── local_llm.py             # 本地LLM调用封装
│   ├── geo_service.py           # GEO模型服务（SentimentService + RecommendationService）
│   ├── kg_extraction/           # KG抽取模型
│   ├── question_generation/     # 问题生成模型（训练目标）
│   ├── question_rewrite/        # 问题改写模型
│   ├── question_evaluation/     # 问题评估模型
│   ├── embedding/               # Embedding模型
│   ├── sentiment/               # 情感分析模型（GEO用）
│   └── recommendation/          # 建议生成模型（GEO用）
│
├── platforms/                   # AI平台API客户端（GEO用）
│   ├── base.py                  # 客户端基类 + AIClientFactory
│   ├── deepseek.py              # DeepSeek API
│   ├── qwen.py                  # 通义千问 API
│   ├── kimi.py                  # Kimi API
│   ├── doubao.py                # 豆包 API
│   └── yuanbao.py               # 元宝 API
│
├── config/                      # 配置模块
│   ├── settings.py              # 全局设置
│   ├── prompts.py               # Prompt模板加载器
│   ├── crawler_config.py        # 爬虫配置加载器
│   └── geo_config.py            # GEO配置（引用规则、权重、域名映射）
│
├── utils/                       # 工具模块
│   ├── batch_output.py          # 批处理增量输出
│   ├── document_utils.py        # 文档处理工具
│   ├── json_parser.py           # JSON解析工具
│   ├── geo_analyze.py           # GEO分析工具（AnalyzeTool + CitationAnalyzer）
│   ├── geo_chart.py             # GEO图表生成（5个统计图表）
│   └── geo_query.py             # GEO查询工具（QueryTool）
│
├── data/                        # 数据目录
│   ├── crawl_configs/           # 爬虫配置
│   │   └── {品牌名}_config.json  # 品牌爬取配置
│   ├── domain_configs/          # 领域配置
│   │   ├── question_types.json  # 问题类型配置
│   │   └── competitors.json     # 竞品配置
│   ├── prompts/                 # Prompt模板文件
│   │   ├── kg_extraction_{domain}.md  # KG抽取Prompt
│   │   ├── question_generation.md      # 问题生成Prompt
│   │   ├── question_rewrite.md         # 问题改写Prompt
│   │   ├── question_quality_eval.md    # 问题评估Prompt
│   │   ├── text_cleaning.md            # 文本清洗Prompt
│   │   ├── geo_analysis_prompt.md      # GEO分析Prompt（LLM精确分析）
│   │   └── recommendation_prompt.md    # GEO建议生成Prompt（外部文件）
│   ├── keywords/                # NER规则配置
│   │   ├── medicine_keywords.json
│   │   ├── electronics_keywords.json
│   │   ├── food_keywords.json
│   │   └── fashion_keywords.json
│   ├── batch_output/            # 批处理输出目录
│   │   └ {run_id}/batch_*.json  # 批次文件
│   └ authority/                  # GEO权威性配置（可选）
│
├── output/                      # 输出目录
│   ├── incremental/             # 增量问题输出
│   ├── charts/                  # GEO图表输出（5个PNG文件）
│   └ questions.json           # 最终问题输出
│
├── SFT/                         # SFT训练配置
│   └ train_config.yaml          # 训练参数
│   └ sft_alpaca_train.json      # SFT训练数据
│
├── GRPO/                        # GRPO训练配置
│   ├── grpo_config.yaml         # GRPO参数
│   ├── reward_function.py       # 奖励函数
│   └ grpo_data.json             # GRPO训练数据
│
├── milvus_data/                 # Milvus Lite数据目录
│   └ milvus.db                  # Milvus Lite数据库
│
├── requirements.txt             # 依赖列表
├── .env.example                 # 环境变量示例
└ README.md                      # 项目文档
```

---

## 环境配置

### 依赖安装

```bash
conda create -n question_generation_env python=3.11
conda activate question_generation_env
pip install -r requirements.txt
```

### 环境变量

复制 `.env.example` 到 `.env`：

```bash
cp .env.example .env
```

关键配置项：

| 配置项 | 说明 |
|-------|------|
| KG_MODEL_PATH | KG抽取模型路径 |
| QG_MODEL_PATH | 问题生成模型路径 |
| QR_MODEL_PATH | 问题改写模型路径 |
| QE_MODEL_PATH | 问题评估模型路径 |
| EMBEDDING_MODEL_PATH | Embedding模型路径 |
| SENTIMENT_MODEL_PATH | GEO情感分析模型路径 |
| RECOMMENDATION_MODEL_PATH | GEO建议生成模型路径 |
| RECOMMENDATION_PROMPT_PATH | GEO建议生成Prompt文件路径 |
| GEO_ANALYSIS_MODEL_PATH | GEO分析LLM模型路径（用于精确提取指标） |
| GEO_ANALYSIS_PROMPT_PATH | GEO分析Prompt文件路径 |
| GEO_ANALYSIS_USE_LLM | 是否使用LLM进行分析（替代正则方案） |
| GEO_ANALYSIS_FALLBACK | LLM失败时是否回退到正则方案 |
| MILVUS_HOST | Milvus地址 |
| GEO平台API Keys | DeepSeek/Qwen/Kimi/Doubao/Yuanbao |

---

## 快速开始

### 1. 安装 Milvus

```bash
pip install milvus-lite
```

配置 `.env`：
```bash
MILVUS_HOST=./milvus_data/milvus.db
```

### 2. 创建爬虫配置

在 `data/crawl_configs/` 创建 `君乐宝_config.json`：

```json
{
    "official_site": {
        "enabled": true,
        "base_url": "https://www.junlebaoruye.com",
        "target_pages": [
            {"path": "/introduction/detail/1.html", "category": "品牌介绍"}
        ]
    },
    "zhihu": {
        "enabled": false,
        "search_keywords": ["君乐宝奶粉"],
        "max_items": 30
    }
}
```

### 3. 爬取并生成问题

```bash
nohup python -u  main.py --mode crawl --brand 华为 --domain electronics --include-geo --output output/questions.json >| /root/workspace/Question_Generation/geo_tracker_output.log 2>&1 &
```

### 4. 从已有知识库生成问题（含GEO）

```bash
nohup python -u main.py --mode generate --brand 君乐宝 --domain food --include-geo --output output/questions.json >| /root/workspace/Question_Generation/geo_tracker_output.log 2>&1 &
```

---

## 运行模式详解

| 模式 | 命令 | 说明 |
|-----|------|------|
| **crawl** | `--mode crawl` | 爬取数据 + 构建知识库 + 生成问题 |
| **generate** | `--mode generate` | 从已有知识库生成问题 |
| **add** | `--mode add` | 增量添加数据 |
| **remove** | `--mode remove` | 删除数据 |
| **update** | `--mode update` | 更新数据 |
| **list** | `--mode list` | 查看知识库统计 |

---

## crawl模式完整流程

执行 `python main.py --mode crawl --brand 君乐宝 --domain food --include-geo`：

### 步骤1：系统配置加载

```
读取文件:
  - .env --> 环境变量
  - config/settings.py --> Settings对象
  - data/crawl_configs/君乐宝_config.json --> 爬虫配置
```

### 步骤2：数据处理Agent

```
读取文件:
  - data/keywords/food_keywords.json --> NER规则
  - data/prompts/kg_extraction_food.md --> KG抽取Prompt
  
生成文件:
  - data/batch_output/{run_id}/batch_0000.json --> 批次文件（每50个文档）
  - data/batch_output/{run_id}/batch_0001.json
  - ...

模型调用:
  - models/kg_extraction/ --> KG抽取模型
```

### 步骤3：向量索引Agent

```
读取文件:
  - data/batch_output/{run_id}/batch_*.json --> 所有批次文件
  
生成存储:
  - Milvus Collection: external_kb_君乐宝
  
模型调用:
  - models/embedding/ --> Embedding模型
```

### 步骤4：问题生成循环

```
读取存储:
  - Milvus Collection: external_kb_君乐宝 --> 逐块读取
  
读取文件:
  - data/prompts/question_generation.md --> 问题生成Prompt
  - data/domain_configs/question_types.json --> 问题类型配置
  
生成文件:
  - output/incremental/{run_id}/questions/questions_*.json --> 增量问题
  
模型调用:
  - models/question_generation/ --> 问题生成模型（训练目标）
```

### 步骤5：批量客观评估

```
读取数据:
  - generated_questions列表 --> 待评估问题
  
输出:
  - objective_filtered_questions --> 过滤后问题
```

### 步骤6：批量改写

```
读取文件:
  - data/prompts/question_rewrite.md --> 改写Prompt
  
输出:
  - question_pairs列表
  
模型调用:
  - models/question_rewrite/ --> 改写模型
```

### 步骤7：批量主观评估

```
读取文件:
  - data/prompts/question_quality_eval.md --> 评估Prompt
  
输出:
  - 最终question_pairs
  
模型调用:
  - models/question_evaluation/ --> 评估模型
```

### 步骤8：GEO追踪分析（--include-geo）

```
调用API:
  - platforms/deepseek.py --> DeepSeek API
  - platforms/qwen.py --> 通义千问 API
  - platforms/kimi.py --> Kimi API
  - platforms/doubao.py --> 豆包 API
  - platforms/yuanbao.py --> 元宝 API

读取文件:
  - data/prompts/recommendation_prompt.md --> 建议生成Prompt（外部文件）
  
读取配置:
  - config/geo_config.py --> 引用分类规则、权重配置
  
模型调用:
  - models/sentiment/ --> 情感分析模型（微调RoBERTa，3分类）
  - models/recommendation/ --> 建议生成模型（微调LLM）
  
生成文件:
  - output/charts/platform_mention_rate.png --> 提及率图表
  - output/charts/platform_rank_rates.png --> 排名率图表
  - output/charts/platform_sentiment.png --> 情感分布图表
  - output/charts/platform_visibility_score.png --> 可见性分数图表
  - output/charts/platform_citation_analysis.png --> 引用分析图表
  
生成存储:
  - Milvus Collection: geo_analysis_君乐宝 --> GEO详细结果
  - 主Collection geo_*字段 --> 汇总统计（每个平台独立字段）
```

### 步骤9：最终输出

```
生成文件:
  - output/questions.json --> 最终问题对汇总
  - SFT/sft_alpaca_train.json --> SFT训练数据（可选）
  - GRPO/grpo_data.json --> GRPO训练数据（可选）
```

---

## GEO追踪分析

GEO追踪分析完全复制 GEO_Tracker 项目功能，仅将数据存储从 SQLite 改为 Milvus。

### 核心功能

| 功能 | 实现文件 | 说明 |
|------|---------|------|
| **平台API调用** | platforms/*.py | 5个AI平台API客户端 |
| **GEO指标分析** | models/geo_service.py - GEOAnalysisService | LLM精确分析（替代正则方案） |
| **情感分析** | models/geo_service.py - SentimentService | 微调RoBERTa模型（3分类：positive/neutral/negative） |
| **建议生成** | models/geo_service.py - RecommendationService | 微调LLM模型，读取外部prompt文件 |
| **引用分析** | utils/geo_analyze.py - CitationAnalyzer | 完整引用分析 + gap analysis |
| **图表生成** | utils/geo_chart.py | 生成5个统计图表PNG文件 |

### 外部Prompt文件

| Prompt文件 | 用途 |
|-----------|------|
| recommendation_prompt.md | 建议生成模型输入（优化建议） |
| geo_analysis_prompt.md | GEO分析模型输入（精确提取各项指标） |

环境变量配置：
```bash
RECOMMENDATION_PROMPT_PATH=./data/prompts/recommendation_prompt.md
GEO_ANALYSIS_PROMPT_PATH=./data/prompts/geo_analysis_prompt.md
```

### LLM分析方案（推荐）

GEO指标提取支持两种方案：

| 方案 | 配置 | 说明 |
|------|------|------|
| **LLM分析** | `GEO_ANALYSIS_USE_LLM=true` | 使用LLM精确提取所有指标（推荐） |
| **正则分析** | `GEO_ANALYSIS_USE_LLM=false` | 使用正则匹配（备选方案） |
| **自动回退** | `GEO_ANALYSIS_FALLBACK=true` | LLM失败时自动回退到正则 |

**LLM方案优势：**
- 能识别"首选"、"最推荐"等语义表达，准确判断排名
- 能分析上下文情感，而非整体回答情感
- 能判断引用的相关性和权威性
- 能做差距分析，给出具体优化建议
- 输出结构化JSON，格式稳定

### 提取的指标列表

| 类别 | 字段 | 说明 |
|------|------|------|
| 品牌提及 | mentioned, rank, mention_count, first_mention_at, mention_position | 是否提及、排名、次数、位置 |
| 情感分析 | sentiment, sentiment_score, sentiment_words | 情感倾向、强度、关键词 |
| 竞品分析 | competitors_found, competitor_ranks, competitor_total, competitor_details | 发现的竞品及其排名 |
| 引用分析 | brand_citations, brand_website_cited, competitor_citations, citation_authority_score, citation_types | 品牌引用、竞品引用、权威度 |
| 差距分析 | citation_gap_analysis, opportunities | 引用差距和优化机会 |

### 生成的图表文件

| 图表文件 | 说明 |
|---------|------|
| platform_mention_rate.png | 各平台提及率柱状图 |
| platform_rank_rates.png | 排名率对比（第一率、前三率、前五率） |
| platform_sentiment.png | 情感分布对比 |
| platform_visibility_score.png | 可见性分数对比 |
| platform_citation_analysis.png | 引用分析对比 |

### 分析原则

1. **所有问题同等对待**：主问题和改写问题不区分
2. **每个平台独立统计**：不跨平台汇总，每个平台有独立字段
3. **引用差距分析**：分析排名更高的竞品引用来源

### GEO配置（.env）

```bash
GEO_ENABLED=false
GEO_PLATFORMS=deepseek,qwen,kimi,doubao,yuanbao
SENTIMENT_MODEL_PATH=./models/sentiment
RECOMMENDATION_MODEL_PATH=./models/recommendation
RECOMMENDATION_PROMPT_PATH=./data/prompts/recommendation_prompt.md

# GEO分析LLM配置（用于精确提取指标）
GEO_ANALYSIS_MODEL_PATH=./models/question_evaluation
GEO_ANALYSIS_PROMPT_PATH=./data/prompts/geo_analysis_prompt.md
GEO_ANALYSIS_USE_LLM=true
GEO_ANALYSIS_FALLBACK=true

# GEO平台API Keys
DEEPSEEK_API_KEY=
QWEN_API_KEY=
KIMI_API_KEY=
DOUBAO_API_KEY=
YUANBAO_API_KEY=
```

---

## 模型说明

| 模型 | 是否训练 | 调用时机 |
|------|---------|---------|
| kg_extraction | ❌ 不训练 | 步骤2：KG抽取 |
| question_generation | ✅ **训练目标** | 步骤4：问题生成 |
| question_rewrite | ❌ 不训练 | 步骤6：问题改写 |
| question_evaluation | ❌ 不训练 | 步骤7：主观评估 |
| embedding | ❌ 不训练 | 步骤3：向量索引 |
| sentiment | ❌ 不训练 | 步骤8：GEO情感分析 |
| recommendation | ❌ 不训练 | 步骤8：GEO建议生成 |

---

## 输出格式

### QuestionPair结构

```json
{
  "id": "qp_block_001_0",
  "block_id": "block_001",
  "brand_name": "君乐宝",
  "primary_question": "什么奶粉含有活性免疫球蛋白？",
  "question_type": "成分问询",
  "rewritten_questions": ["含有活性免疫球蛋白的奶粉有哪些？", ...],
  "entity_tags": ["活性免疫球蛋白", "奶粉"],
  "evaluation_metrics": {
    "objective_score": 85,
    "subjective_score": 90,
    "total_score": 87.5
  }
}
```

### GEO分析汇总

```json
{
  "geo_summary": {
    "total_blocks": 50,
    "total_questions": 120,
    "chart_paths": {
      "mention_rate": "output/charts/platform_mention_rate.png",
      "rank_rates": "output/charts/platform_rank_rates.png",
      "sentiment": "output/charts/platform_sentiment.png",
      "visibility_score": "output/charts/platform_visibility_score.png",
      "citation": "output/charts/platform_citation_analysis.png"
    },
    "recommendations": [
      {"category": "内容优化", "priority": "高", "action": "..."}
    ],
    "platform_stats": {
      "deepseek": {"mentioned_count": 45, "avg_rank": 2.3, "mention_rate": 0.375}
    }
  }
}
```

---

## 许可证

MIT License