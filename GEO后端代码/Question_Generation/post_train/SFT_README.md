1. 克隆 LLaMA Factory

  git clone https://github.com/hiyouga/LLaMA-Factory.git
  cd LLaMA-Factory
  pip install -e ".[torch,metrics]"

  2. 注册数据集

  编辑 LLaMA-Factory/data/dataset_info.json，在末尾添加：


  2. 注册数据集

  编辑 LLaMA-Factory/data/dataset_info.json，在末尾添加：

  "question_gen": {
    "file_name": "D:/实习/GEO_Tracker_System/Question_Generation/SFT/sft_alpaca_train.json",
    "formatting": "alpaca",
    "columns": {
      "prompt": "instruction",
      "query": "input",
      "response": "output"
    }
  }

  3. 训练
   export PATH="$CONDA_PREFIX/bin:$PATH"
   source ~/.bashrc

# Web UI界面训练
CUDA_VISIBLE_DEVICES=1 llamafactory-cli webui

# save_best
val_size = 0.1
Extra configurations/Extra arguments
{"load_best_model_at_end": true, "metric_for_best_model": "eval_loss", "greater_is_better": false, "save_total_limit": 3}
