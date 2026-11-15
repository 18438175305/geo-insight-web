# GEO Insight · AI品牌可见性监测平台

当用户向 DeepSeek、通义千问、Kimi、豆包、元宝提问"什么手机拍照好"时，AI 的回答里会不会提到你的品牌？排第几？GEO Insight 用一条 Multi-Agent 流水线回答这个问题：自动生成"刻意隐藏品牌名"的探针问题，投放五大 AI 平台，量化品牌可见性。

## 仓库结构

```
├── source前端代码/     # Web 前端（五页交互 + 自动演示模式）
└── GEO后端代码/        # GEO 品牌监测系统后端（LangGraph Multi-Agent + SFT/GRPO训练）
```

## 前端（source前端代码/）

- 五个页面：监测总览 / 品牌体检 / 探针问题库（18品牌） / AI回答洞察 / 智能体编排
- 内置「▶ 自动演示」模式：自动巡游五页并配同步讲解字幕
- 运行：`python3 scripts/serve.py` → http://127.0.0.1:8080（或直接打开 `dist/index.html`）
- 技术栈：HTML/CSS + 原生 JavaScript + SVG 图表，Hash 路由，零第三方依赖

## 后端（GEO后端代码/）

GEO 品牌监测系统（LangGraph 状态机 + 8 Agent 协作）：

- 数据层：4 类爬虫（官网/知乎/小红书/白皮书）→ 清洗分块 → NER+LLM 知识图谱抽取 → Milvus 向量库
- 生成层：问题生成 Agent（Qwen2.5-7B，SFT 2457 条 + GRPO 2002/811 条训练）→ 双重评估过滤 → 改写
- 分析层：GEO 追踪 Agent（DeepSeek/通义千问/Kimi/豆包/元宝五平台）→ 五维可见性评分（提及/排名/位置/引用/情感）
- `post_train/sft_training_summary/` 保留真实训练产出（损失曲线、训练日志、结果JSON）
- 说明：训练权重、完整训练数据及核心提示词/关键实现因保密与体积原因未随仓库公开（可应评审要求线下展示）；SFT/GRPO 基于开源框架 LlamaFactory 与 verl，仓库保留数据转换脚本、真实运行产物与训练产出摘要

## 团队信息

| 项目 | 内容 |
| --- | --- |
| 学校 | 西安交通大学 |
| 参赛组别 | 研究生组 |
| 团队名称 | 慧见 |
| 队员 | 陈园方、张伊婕 |
