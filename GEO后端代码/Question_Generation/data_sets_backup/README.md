# SFT数据集构建Pipeline

多品牌多领域SFT训练数据构建工具（使用本地模型）。

## 目标

- 每个领域 **500条** 高质量训练数据
- 4个领域：medicine, electronics, food, fashion
- 总计 **2000条** SFT训练数据

## 目录结构

```
datasets/
├── configs/
│   ├── brand_configs.json          # 完整品牌配置（含爬虫配置）
│   └── brand_configs_simple.json   # 简化品牌配置
│
├── scripts/
│   ├── crawl_multi_domain_data.py  # 步骤1: 多领域数据爬取
│   ├── preprocess_data.py          # 步骤2: 预处理与KG抽取
│   ├── generate_sft_candidates.py  # 步骤3: 本地模型生成候选问题，拆分SFT/GRPO
│   ├── validate_sft_data.py        # 步骤4: 生成人工审核文件（SFT和GRPO）
│   ├── convert_to_grpo.py          # 步骤4.6: GRPO数据格式转换
│   ├── format_sft_data.py          # 步骤5: 格式化最终数据
│   ├── convert_to_alpaca.py        # 步骤6: 转成Alpaca格式
│   └── run_pipeline.py             # 主Pipeline入口
│
└── output/
    ├── crawled_data/               # 爬取原始数据
    ├── preprocessed_data/          # 预处理后的数据
    ├── sft_candidates/             # SFT候选数据
    ├── grpo_candidates/            # GRPO候选数据
    ├── validated_data/             # 验证后的数据
    │   ├── sft_data_for_human_review.csv   # SFT人工审核文件
    │   ├── grpo_data_for_human_review.csv  # GRPO人工审核文件
    │   ├── sft_valid_data.json             # SFT有效数据
    │   ├── grpo_valid_data.json            # GRPO有效数据
    │   └── grpo_train_format.json          # GRPO训练格式数据
    └── final_sft_dataset/          # 最终SFT训练数据
```

## 使用方法

### 1. 运行完整Pipeline

```bash
# 执行所有步骤
python datasets/scripts/run_pipeline.py

# 指定领域
python datasets/scripts/run_pipeline.py --domains medicine electronics

# 生成人工审核文件
python datasets/scripts/run_pipeline.py --review
```

### 2. 分步执行

```bash
# 步骤1: 爬取数据
nohup python -u datasets/scripts/run_pipeline.py --step 1 >| /root/workspace/Question_Generation/datasets/step1_output.log 2>&1 &

# 步骤2: 预处理与KG抽取
nohup python -u datasets/scripts/run_pipeline.py --step 2 >| /root/workspace/Question_Generation/datasets/output/step2_output.log 2>&1 &
python datasets/scripts/run_pipeline.py --step 2 --no-llm-kg 

# 步骤3: 本地模型生成候选问题（自动拆分SFT和GRPO）
nohup python -u datasets/scripts/run_pipeline.py --step 3 >| /root/workspace/Question_Generation/datasets/output/step3_output.log 2>&1 &

# 步骤4: 生成人工审核文件（SFT和GRPO各一份）
python datasets/scripts/run_pipeline.py --step 4 --review

# 步骤4.5: 导入人工审核结果（SFT和GRPO分别导入）
python datasets/scripts/validate_sft_data.py --import-review

# 步骤4.6: GRPO数据格式转换
python datasets/scripts/convert_to_grpo.py

# 步骤5: 格式化SFT最终数据
python datasets/scripts/run_pipeline.py --step 5

# 步骤6: 转成适合llamafactory的alpaca格式
python datasets/scripts/convert_to_alpaca.py
```

### 3. 人工审核流程

```bash
# 1. 生成审核文件（SFT和GRPO各一份）
python datasets/scripts/run_pipeline.py --step 4 --review

# 2. 打开 output/validated_data/sft_data_for_human_review.csv
#    在 is_valid 列填写 1(通过) 或 2(拒绝)
# 3. 打开 output/validated_data/grpo_data_for_human_review.csv
#    在 is_valid 列填写 1(通过) 或 2(拒绝)

# 4. 导入审核结果（SFT和GRPO分别导入）
python datasets/scripts/validate_sft_data.py --import-review

# 5. GRPO数据格式转换
python datasets/scripts/convert_to_grpo.py

# 6. 继续后续步骤
python datasets/scripts/run_pipeline.py --step 5
python datasets/scripts/convert_to_alpaca.py
```

## SFT数据格式

### 输入格式（Prompt）

```
品牌名称: 云南白药
领域: medicine
文本内容: 云南白药具有止血、消炎的功效...
KG实体: ["云南白药", "止血", "消炎"]
KG关系: ["具有功效", "用于场景"]
```

### 输出格式（JSON数组）

```json
[
  {
    "question": "什么产品有止血消炎的功效？",
    "question_type": "功效问询",
    "target_entity": "止血",
    "competitor_mentioned": ""
  }
]
```

## 验证规则

1. **格式验证**: 必需字段完整性检查
2. **内容验证**: 
   - 品牌名泄露检测（问题中不应出现品牌名）
   - 问题长度检查（10-100字符）
   - 与源内容关联性检查
3. **类型验证**: 问题类型需属于该领域有效类型

## 领域问题类型

| 领域 | 问题类型 |
|------|----------|
| medicine | 功效问询、用法问询、禁忌问询、推荐问询 |
| electronics | 功能问询、参数问询、场景问询、对比问询、推荐问询 |
| food | 成分问询、口味问询、营养问询、场景问询、推荐问询 |
| fashion | 材质问询、风格问询、功能问询、场景问询、推荐问询 |

## 注意事项

1. 爬虫数据可能需要人工补充，部分品牌官网不支持爬取
2. KG抽取可选择是否使用LLM（`--no-llm-kg` 参数）
3. 问题生成使用项目中的本地模型（`get_question_generation_llm()`）
4. 建议使用人工审核文件进行数据质量把关
5. 最终数据量取决于爬取数据质量和模型生成质量

## 输出文件

- `sft_all_domains_train.json`: 合并所有领域的训练数据
- `sft_{domain}_train.json`: 各领域单独的训练数据文件
