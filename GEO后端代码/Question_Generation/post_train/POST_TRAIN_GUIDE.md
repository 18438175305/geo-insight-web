# 后训练指导文档（SFT + GRPO）

> 本文档涵盖：SFT训练结果分析、调优建议、模型合并（WebUI）、SFT效果评估、GRPO训练、GRPO效果评估全流程。

---

## 目录

1. [SFT训练结果解读](#1-sft训练结果解读)
2. [调优建议](#2-调优建议)
3. [模型合并（WebUI）](#3-模型合并webui)
4. [SFT效果评估（学术论文标准）](#4-sft效果评估学术论文标准)
5. [GRPO训练（VERL框架）](#5-grpo训练verl框架)
6. [GRPO效果评估（学术论文标准）](#6-grpo效果评估学术论文标准)

---

## 1. SFT训练结果解读

### 1.1 训练概况

| 项目 | 值 |
|------|-----|
| 基座模型 | Qwen2.5-7B-Instruct |
| 微调方式 | LoRA (rank=8, alpha=16) |
| 训练数据 | question_gen (7,249条训练+验证, 811条独立测试) |
| 训练轮数 | 3 epochs (1,362 steps) |
| 有效batch size | 16 (2 per device × 8 gradient accumulation) |
| 学习率 | 5e-5, cosine scheduler |
| 最终train_loss | 0.331 |
| 最终eval_loss | 0.347 |
| **Best checkpoint** | **step 900 (epoch ≈ 2), eval_loss=0.347** |

### 1.2 saves目录文件说明

#### 根目录文件

| 文件 | 作用 |
|------|------|
| `adapter_model.safetensors` | **最终LoRA权重**（从best checkpoint-900加载） |
| `adapter_config.json` | LoRA配置（rank=8, alpha=16, 目标模块q/k/v/o/gate/up/down_proj） |
| `all_results.json` | 训练+评估综合结果摘要 |
| `train_results.json` | 训练指标（train_loss=0.331, 耗时10653秒） |
| `eval_results.json` | 评估指标（eval_loss=0.347） |
| `trainer_state.json` | 完整训练状态（每10步的loss、学习率、梯度范数、所有eval结果） |
| `training_args.yaml` | 所有训练超参数的可读版本（**WebUI的参数都记录在这里**） |
| `training_args.bin` | 训练参数的二进制版本（用于断点续训） |
| `training_loss.png` | 训练loss曲线图 |
| `training_eval_loss.png` | 验证loss曲线图 |
| `trainer_log.jsonl` | JSONL格式的结构化训练日志 |
| `running_log.txt` | 完整运行日志（含模型加载、数据加载、每步输出） |
| `llamaboard_config.yaml` | LlamaBoard WebUI的配置快照 |
| `README.md` | 模型卡片 |
| Tokenizer文件 | `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`, `added_tokens.json`, `vocab.json`, `merges.txt`, `chat_template.jinja` |

#### Checkpoint目录（checkpoint-900, checkpoint-1300, checkpoint-1362）

每个checkpoint是训练到该步时的完整快照，额外包含：

| 文件 | 作用 |
|------|------|
| `adapter_model.safetensors` | 该步的LoRA权重 |
| `adapter_config.json` | 适配器配置 |
| `optimizer.pt` | 优化器状态（断点续训用） |
| `scheduler.pt` | 学习率调度器状态 |
| `rng_state.pth` | 随机数生成器状态 |
| `trainer_state.json` | 截至该步的训练状态 |
| `training_args.bin` | 训练参数 |

> **注意**：由于设置了 `save_total_limit=3`，只保留了最近的3个checkpoint。最终保存的 `adapter_model.safetensors` 是从 **checkpoint-900（best model）** 加载的。

### 1.3 训练过程分析

**Loss变化趋势**：

| 阶段 | Step | Train Loss | Eval Loss | 状态 |
|------|------|-----------|-----------|------|
| 初始 | 10 | 1.214 | - | 快速下降 |
| Epoch 0.5 | 200 | 0.361 | 0.381 | 持续下降 |
| Epoch 1.0 | 454 | ~0.34 | - | 下降放缓 |
| Epoch 1.5 | 700 | 0.324 | 0.350 | 下降放缓 |
| **Epoch 2.0 (best)** | **900** | **0.291** | **0.347** | **最佳eval_loss** |
| Epoch 2.5 | 1200 | 0.273 | 0.350 | train继续降, eval持平 |
| Epoch 3.0 | 1362 | 0.272 | 0.350 | **过拟合** |

**关键发现**：
- eval_loss在step 900之后不再下降，而train_loss继续下降 → **典型的过拟合信号**
- 第3个epoch对模型质量没有帮助，白白浪费了训练时间

---

## 2. 调优建议

### 2.1 问题诊断

当前效果不好的主要原因（按重要性排序）：

1. **LoRA rank=8 太低** — 7B模型用rank=8容量不足，学不到复杂的生成模式
2. **cutoff_len=2048 太短** — 你的prompt非常长（含品牌信息、KG实体、关系、竞品、生成要求），2048 token很可能会截断
3. **学习率 5e-5 偏高** — 容易不稳定或过拟合
4. **训练3个epoch过多** — 数据集7249条不算大，2个epoch已经过拟合
5. **没有warmup** — 训练初期不稳定

### 2.2 推荐配置（WebUI中修改）

在LlamaFactory WebUI中，按以下参数重新训练：

```
模型名称: Qwen2.5-7B-Instruct
微调方法: lora
模板: qwen
数据集: question_gen

=== 关键参数修改 ===
LoRA rank (lora_rank): 16          (原8 → 16，增大适配器容量)
LoRA alpha (lora_alpha): 32         (原16 → 32，保持 alpha = 2 × rank)
最大长度 (cutoff_len): 4096         (原2048 → 4096，避免截断)
学习率 (learning_rate): 2e-5        (原5e-5 → 2e-5，降低防止过拟合)
训练轮数 (num_train_epochs): 2      (原3 → 2，避免过拟合)
Warmup步数 (warmup_steps): 50       (原0 → 50，稳定训练初期)

=== 保持不变的参数 ===
批大小 (batch_size): 2
梯度累积 (gradient_accumulation_steps): 8
验证集比例 (val_size): 0.1
学习率调度: cosine
计算精度: bf16

=== Extra configurations ===
{
  "load_best_model_at_end": true,
  "metric_for_best_model": "eval_loss",
  "greater_is_better": false,
  "save_total_limit": 3
}
```

### 2.3 如果显存充足，可以进一步优化

```
LoRA rank: 32
LoRA alpha: 64
cutoff_len: 8192
batch_size: 4（需要更多显存）
```

### 2.4 其他优化方向

- **数据质量**：检查SFT数据中是否有低质量输出（如问题与输入内容不匹配、格式不规范等）
- **数据多样性**：确保不同品牌、不同领域的数据均匀分布
- **输出格式**：当前有些output只生成了1个问题，而prompt要求生成3-5个，这会降低训练质量

---

## 3. 模型合并（WebUI）

SFT训练完成后，LoRA适配器需要合并到基座模型中，生成完整的独立模型。后续GRPO训练需要用这个合并后的完整模型。

### 3.1 通过WebUI导出（推荐）

在服务器上启动WebUI：

```bash
cd /path/to/LlamaFactory-main
CUDA_VISIBLE_DEVICES=0 llamafactory-cli webui
```

在WebUI中切换到 **Export** 页签，按以下配置填写：

```
模型名称 (Model name): Qwen2.5-7B-Instruct
微调方法 (Finetuning method): lora
适配器路径 (Adapter path): saves/Qwen2.5-7B-Instruct/lora/train_2026-05-27-23-28-57
    （选择你最新的训练输出目录）

导出目录 (Export dir): /data/ypq/cyf/Question_Generation/models/Qwen2.5-7B-Instruct-SFT
    （合并后模型的保存路径）

导出大小 (Export size): 2
    （每个分片文件的最大GB数）
导出设备 (Export device): auto
导出精度 (Export dtype): float16
```

点击 **Export** 按钮即可。

### 3.2 验证合并后的模型

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_path = "/data/ypq/cyf/Question_Generation/models/Qwen2.5-7B-Instruct-SFT"
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype="auto", device_map="auto")

messages = [{"role": "user", "content": "你的测试prompt"}]
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=512, do_sample=True, temperature=0.7)
print(tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True))
```

---

## 4. SFT效果评估（学术论文标准）

### 4.1 独立测试集

**已划分完成**。原8060条数据已按以下规则划分为：

- `sft_alpaca_train.json` — **7,249条**（训练+验证集，WebUI中 `val_size=0.1` 会自动从中划出验证集）
- `sft_test_set.json` — **811条**（独立测试集，**完全不参与训练**）

划分规则：
1. 按 `input` 字段去重分组（同一input的所有条目必须分到同一集合，避免数据泄露）
2. 按**品牌分层**随机划分（每个品牌取约10%组进入测试集，确保18个品牌都有测试样本）
3. 已验证训练集和测试集的input无任何交叉（交叉数=0）

### 4.2 自动评估指标

| 指标类别 | 具体指标 | 说明 |
|----------|----------|------|
| **格式合规性** | JSON Format Rate | 输出能被正确解析为JSON数组的比例 |
| | Field Completeness Rate | JSON包含所有必需字段(question, question_type, target_entity)的比例 |
| **品牌名隐蔽性** | Brand Leak Rate | 生成中出现品牌名的比例（**越低越好**） |
| | Target Entity Avoidance Rate | target_entity不是品牌名的比例 |
| **内容质量** | BLEU-4 | 生成文本与参考文本的4-gram重叠度 |
| | ROUGE-L | 最长公共子序列匹配 |
| | BERTScore | 语义相似度 |
| **多样性** | Type Diversity | 生成的问题类型分布（10种类型的覆盖率） |
| | Unique Question Rate | 不同prompt生成的问题不重复的比例 |
| **相关性** | Entity Overlap Rate | 生成的target_entity与输入KG实体有重叠的比例 |

#### 评估脚本使用

```bash
python eval_sft.py \
  --base_model /data/ypq/cyf/Question_Generation/models/Qwen2.5-7B-Instruct \
  --sft_model /data/ypq/cyf/Question_Generation/models/Qwen2.5-7B-Instruct-SFT \
  --test_data sft_test_set.json \
  --max_samples 200 \
  --output eval_sft_results.json
```

### 4.3 人工评估

随机抽取100-200条测试样本，让标注人员从以下维度打分（1-5 Likert Scale）：

| 维度 | 5分（优秀） | 3分（一般） | 1分（差） |
|------|------------|------------|----------|
| **流畅性** | 问题自然流畅，语法完全正确 | 基本通顺，有小语病 | 不通顺，难以理解 |
| **相关性** | 问题与输入信息高度相关 | 有一定相关性 | 与输入无关 |
| **隐蔽性** | 完全不提及品牌名，用特征描述引导 | 偶尔接近品牌名边界 | 直接出现品牌名 |
| **引导性** | 能有效引导联想到目标品牌 | 一定程度能联想到 | 无法联想到 |
| **多样性** | 同一输入生成的问题角度丰富 | 有一定变化 | 高度重复 |

建议至少2名标注员独立打分，计算inter-annotator agreement（Cohen's Kappa）。

### 4.4 对比实验设计

| 实验编号 | 方法 | 说明 |
|----------|------|------|
| Exp-1 | Base (Qwen2.5-7B-Instruct) | 原始模型 zero-shot |
| Exp-2 | Base + Few-shot (3-shot) | 原始模型，prompt中给出3个示例 |
| Exp-3 | SFT (LoRA rank=8) | 当前训练结果 |
| Exp-4 | SFT (LoRA rank=16, optimized) | 按调优建议重新训练的结果 |
| Exp-5 | SFT + GRPO | 在Exp-4基础上做GRPO强化学习 |

### 4.5 论文中需要展示的图表

**Table 1: 自动评估指标对比**

| Method | JSON Format↑ | Brand Leak↓ | Field Complete↑ | BLEU-4↑ | ROUGE-L↑ | Type Diversity↑ |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|
| Base (zero-shot) | | | | | | |
| Base (few-shot) | | | | | | |
| SFT (rank=8) | | | | | | |
| SFT (rank=16) | | | | | | |
| SFT + GRPO | | | | | | |

**Table 2: 人工评估结果（平均分±标准差）**

| Method | Fluency | Relevance | Stealthiness | Guidability | Diversity |
|--------|---------|-----------|--------------|-------------|-----------|
| Base | | | | | |
| SFT | | | | | |
| SFT+GRPO | | | | | |

**Figure**：
1. Training Loss / Eval Loss曲线
2. 问题类型分布饼图
3. 雷达图（多维度人工评估对比）
4. Case Study（3-5个典型案例的生成差异）

### 4.6 统计显著性检验

```python
from scipy import stats

# 自动指标：paired t-test
t_stat, p_value = stats.ttest_rel(sft_scores, base_scores)
# p < 0.05 表示差异显著

# 人工评估：Wilcoxon signed-rank test（非参数检验，适合Likert评分）
w_stat, p_value = stats.wilcoxon(sft_ratings, base_ratings)
```

---

## 5. GRPO训练（VERL框架）

### 5.1 数据准备（已完成）

#### 数据转换结果

原 `grpo_data.json`（8,024条，conversations格式）已转换为VERL所需的JSONL格式：
- `grpo_data_verl.jsonl` — **2,002条**（去重后，18个品牌全覆盖）

转换后格式示例：

```jsonl
{"prompt": "你是一个专业的品牌相关问题生成专家。...[完整prompt]", "brand_name": "华为"}
{"prompt": "你是一个专业的品牌相关问题生成专家。...[另一个prompt]", "brand_name": "云南白药"}
```

品牌分布：

| 品牌 | 条数 | 品牌 | 条数 |
|------|------|------|------|
| 华为 | 505 | OPPO | 165 |
| 以岭药业 | 296 | 小米 | 149 |
| 索尼 | 233 | 李锦记 | 119 |
| 云南白药 | 94 | 同仁堂 | 85 |
| 统一 | 62 | 洽洽 | 59 |
| 盐津铺子 | 58 | 君乐宝 | 57 |
| 片仔癀 | 52 | 桂林三金 | 31 |
| 联想 | 20 | 波司登 | 9 |
| 华润三九 | 6 | 白象 | 2 |

#### GRPO验证集

GRPO的训练信号来自reward function，不需要传统意义上的验证集loss。但为了在训练过程中实时跟踪模型在未见数据上的表现，已从 `sft_test_set.json`（811条）转换生成 `grpo_val_data.jsonl`（811条，VERL格式），可用于训练过程中定期评估reward变化。

- `grpo_data_verl.jsonl` — **2,002条**（GRPO训练集）
- `grpo_val_data.jsonl` — **811条**（GRPO验证集，训练过程中定期评估reward）

两者数据来源不同（GRPO训练数据来自 `grpo_data.json`，验证数据来自 `sft_test_set.json`），无交叉泄露。训练完成后的最终效果评估同样使用 `sft_test_set.json`。

### 5.2 reward_function.py 改进说明

改进后的打分结构（总分1.0）：

```
品牌名合规:     +0.20  （泄露品牌名直接返回0分）
JSON格式正确:   +0.15
必需字段完整:   +0.15  （question, question_type, target_entity）
类型合法:       +0.15  （question_type必须在10种合法类型中）
每个问题:
  长度合理:     +0.05  （5-100字）
  以问号结尾:   +0.05
  target有效:   +0.05  （非空且非品牌名）
多样性(>=2种):  +0.10  （生成2种以上不同类型的问题）
```

### 5.3 VERL环境配置

在远程服务器上执行：

```bash
# 安装VERL（已完成，版本 0.8.0.dev0）
```

### 5.4 数据格式转换（JSONL → Parquet）

VERL要求数据是parquet格式。在服务器上运行：

```bash
cd /data/ypq/cyf/Question_Generation/post_train
python convert_to_parquet.py
```

这会将 `grpo_data_verl.jsonl` 和 `grpo_val_data.jsonl` 转换为 `.parquet` 格式。

### 5.5 启动GRPO训练

已提供 `run_grpo.sh` 启动脚本，在服务器上执行：

```bash
cd /data/ypq/cyf/Question_Generation/post_train

# 先给脚本执行权限
chmod +x run_grpo.sh

# 启动训练（默认使用4张GPU）
bash run_grpo.sh

# 如果GPU数量不同，修改环境变量：
# NGPUS=2 bash run_grpo.sh        # 使用2张GPU
# NGPUS=8 bash run_grpo.sh        # 使用8张GPU
```

脚本内部使用 `python3 -m verl.trainer.main_ppo` + Hydra override 方式传参（这是VERL 0.8.0.dev0的标准接口）。

关键参数说明：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `ROLLOUT_N` | 5 | 每个prompt生成的response数量 |
| `TRAIN_BATCH_SIZE` | 64 | 全局batch size |
| `MAX_PROMPT_LENGTH` | 3072 | prompt最大长度 |
| `MAX_RESPONSE_LENGTH` | 512 | 生成response最大长度 |
| `ACTOR_LR` | 1e-6 | 学习率 |
| `KL_LOSS_COEF` | 0.001 | KL散度约束系数 |
| `TOTAL_EPOCHS` | 5 | 训练轮数 |
| `NGPUS` | 4 | GPU数量 |

reward function通过以下参数指定：
- `reward.custom_reward_function.path` — reward_function.py的路径
- `reward.custom_reward_function.name` — 入口函数名（`compute_score`）

### 5.6 GRPO训练注意事项

| 注意事项 | 说明 |
|----------|------|
| **SFT模型已合并** | 已放在 `/data/ypq/cyf/Question_Generation/models/Qwen2.5-7B-Instruct-SFT` |
| **reward函数** | 已添加 `compute_score` 入口，VERL会传入含 `prompt` 和 `response` 的字典 |
| **GPU显存** | 7B模型GRPO建议至少2-4张A100 (80GB)，每张约需40-50GB |
| **数据格式** | 必须是parquet，不是JSONL |
| **rollout_n** | 建议设为5（每个prompt生成5个response做组内比较） |

### 5.7 训练过程监控

GRPO训练过程中应关注以下指标：

| 指标 | 含义 | 理想趋势 |
|------|------|----------|
| `reward/mean` | 模型生成的response的平均reward | 持续上升 |
| `reward/variance` | reward方差 | 逐渐收敛 |
| `policy/kl` | 当前策略与参考策略的KL散度 | 保持较小（<0.1） |
| `policy/entropy` | 策略熵 | 缓慢下降但不能太快（太快说明模式崩塌） |
| `loss/policy` | 策略损失 | 下降 |
| `loss/value` | 价值损失 | 下降 |

如果reward不上升或KL急剧增大，需要调低学习率或增大kl_coef。

---

## 6. GRPO效果评估（学术论文标准）

### 6.1 评估思路

GRPO的效果评估核心是回答一个问题：**GRPO强化学习是否让模型在SFT基础上进一步提升了？**

因此需要三组对比：Base → SFT → SFT+GRPO，使用同一个独立测试集 `sft_test_set.json`。

### 6.2 评估数据

使用 `sft_test_set.json`（811条）作为统一测试集。这个测试集：
- 与SFT训练数据无交叉
- 与GRPO训练数据（`grpo_data_verl.jsonl`）无交叉（GRPO的prompt来自不同数据源）
- 18个品牌全覆盖

### 6.3 自动评估指标

在SFT评估指标的基础上，GRPO评估需要额外关注以下指标：

| 指标 | 说明 | GRPO特有的意义 |
|------|------|---------------|
| **Reward Score** | 模型生成结果在reward_function上的平均得分 | 直接衡量GRPO训练目标的达成度 |
| **Brand Leak Rate** | 品牌名泄露率 | GRPO应该比SFT更低（reward函数惩罚泄露） |
| **JSON Format Rate** | JSON格式合规率 | GRPO应该比SFT更高（reward函数奖励格式正确） |
| **Type Validity Rate** | question_type在合法列表中的比例 | GRPO应该比SFT更高（改进的reward增加了type验证） |
| **Type Diversity** | 问题类型分布的多样性 | GRPO应该比SFT更均衡（reward奖励多样性） |
| **Quality Score** | 综合0-1分质量评估 | GRPO应该比SFT更高 |

#### 评估脚本

```bash
# 对比 SFT模型 vs SFT+GRPO模型
python eval_sft.py \
  --base_model /data/ypq/cyf/Question_Generation/models/Qwen2.5-7B-Instruct-SFT \
  --sft_model ./grpo_output/final_model \
  --test_data sft_test_set.json \
  --max_samples 200 \
  --output eval_grpo_results.json
```

#### 额外的GRPO专项评估脚本

在 `eval_sft.py` 输出的基础上，额外计算reward得分：

```python
import json
from reward_function import evaluate_question_quality
import re

def eval_grpo_reward(predictions_file, test_data_file):
    """计算GRPO模型生成结果的平均reward"""
    with open(predictions_file, 'r', encoding='utf-8') as f:
        predictions = json.load(f)
    with open(test_data_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)

    rewards = []
    for pred, item in zip(predictions, test_data):
        # 从input中提取brand_name
        m = re.search(r'品牌名称[：:]\s*(\S+)', item.get('input', ''))
        brand = m.group(1) if m else None
        reward = evaluate_question_quality(pred['response'], brand)
        rewards.append(reward)

    avg_reward = sum(rewards) / len(rewards) if rewards else 0
    print(f"平均Reward: {avg_reward:.4f}")
    print(f"Reward分布: 0.0={sum(1 for r in rewards if r==0)}, 0.0-0.5={sum(1 for r in rewards if 0<r<=0.5)}, 0.5-1.0={sum(1 for r in rewards if 0.5<r<=1.0)}")
    return rewards
```

### 6.4 GRPO训练曲线分析

论文中需要展示GRPO训练过程中的关键曲线：

**Figure: GRPO Training Dynamics**

需要画4张子图：

1. **Reward Curve** — 横轴：training step，纵轴：平均reward。期望：持续上升后趋于平稳
2. **KL Divergence Curve** — 横轴：training step，纵轴：KL(policy || ref)。期望：缓慢上升但保持较小
3. **Policy Entropy Curve** — 横轴：training step，纵轴：策略熵。期望：缓慢下降
4. **Response Length Distribution** — 训练前后response长度分布对比

```python
import matplotlib.pyplot as plt
import json

# 从VERL的训练日志中提取数据（具体格式取决于VERL版本）
# 示例代码：
steps = [...]
rewards = [...]
kl_div = [...]
entropy = [...]

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

axes[0].plot(steps, rewards)
axes[0].set_xlabel('Step')
axes[0].set_ylabel('Mean Reward')
axes[0].set_title('Reward Curve')

axes[1].plot(steps, kl_div)
axes[1].set_xlabel('Step')
axes[1].set_ylabel('KL Divergence')
axes[1].set_title('KL Divergence')

axes[2].plot(steps, entropy)
axes[2].set_xlabel('Step')
axes[2].set_ylabel('Policy Entropy')
axes[2].set_title('Policy Entropy')

plt.tight_layout()
plt.savefig('grpo_training_curves.pdf', dpi=300)
```

### 6.5 GRPO专项对比实验

在论文中，针对GRPO需要做以下消融实验：

**Table 3: GRPO消融实验**

| 设置 | Reward Score↑ | Brand Leak↓ | Type Validity↑ | Type Diversity↑ |
|------|:---:|:---:|:---:|:---:|
| SFT (无GRPO) | | | | |
| SFT + GRPO (无type验证) | | | | |
| SFT + GRPO (无多样性奖励) | | | | |
| SFT + GRPO (完整reward) | | | | |

**Table 4: KL系数影响**

| kl_coef | Reward Score↑ | Brand Leak↓ | BLEU-4↑ | 备注 |
|---------|:---:|:---:|:---:|------|
| 0.01 | | | | 可能偏离SFT太远 |
| 0.05 | | | | 推荐默认值 |
| 0.10 | | | | 更保守，改动更小 |

### 6.6 GRPO效果的综合论证

论文中关于GRPO的论证逻辑：

1. **定量对比**：在同一个测试集上，SFT+GRPO在各项指标上优于SFT
2. **统计显著性**：对关键指标做paired t-test，p < 0.05
3. **训练曲线**：reward上升、KL可控、无模式崩塌
4. **消融实验**：证明reward function中每个组件的贡献
5. **Case Study**：选取典型样本，展示GRPO后模型在格式合规性、品牌名隐蔽性、问题多样性上的提升

```python
# 统计显著性检验
from scipy import stats

sft_rewards = [...]    # SFT模型在测试集上每条的reward
grpo_rewards = [...]   # SFT+GRPO模型在测试集上每条的reward

t_stat, p_value = stats.ttest_rel(grpo_rewards, sft_rewards)
print(f"t={t_stat:.4f}, p={p_value:.6f}")
# p < 0.05 表示GRPO的提升统计显著

# 效果量 (Cohen's d)
import numpy as np
d = (np.mean(grpo_rewards) - np.mean(sft_rewards)) / np.sqrt(
    (np.std(grpo_rewards)**2 + np.std(sft_rewards)**2) / 2
)
print(f"Cohen's d = {d:.4f}")
# d > 0.8 表示大效果量
```

---

## 文件同步清单

以下文件已在本地创建或修改，需要同步到服务器：

| 文件 | 操作 | 说明 |
|------|------|------|
| `sft_alpaca_train.json` | **修改** | 已从中移出测试集，剩余7,249条用于训练+验证 |
| `sft_test_set.json` | **新建** | 独立测试集811条，按品牌分层划分 |
| `grpo_data_verl.jsonl` | **新建** | GRPO训练数据（2,002条去重后的prompt） |
| `grpo_val_data.jsonl` | **新建** | GRPO验证数据（811条） |
| `reward_function.py` | **修改** | 添加了VERL入口函数 `compute_score` |
| `eval_sft.py` | **新建** | 效果自动评估脚本 |
| `convert_to_parquet.py` | **新建** | JSONL→Parquet转换脚本（在服务器上运行） |
| `run_grpo.sh` | **新建** | GRPO启动脚本（适配VERL 0.8.0.dev0接口） |
| `POST_TRAIN_GUIDE.md` | **更新** | 本指导文档 |

同步命令示例：

```bash
scp sft_alpaca_train.json sft_test_set.json grpo_data_verl.jsonl \
    grpo_val_data.jsonl reward_function.py eval_sft.py \
    convert_to_parquet.py run_grpo.sh POST_TRAIN_GUIDE.md \
    user@server:/data/ypq/cyf/Question_Generation/post_train/
```

> **重要**：`sft_alpaca_train.json` 已被修改（移出了测试集），同步时会覆盖原文件，请先备份。
