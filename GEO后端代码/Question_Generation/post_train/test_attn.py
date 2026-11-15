from transformers import AutoConfig

config_path = r"D:\实习\GEO_Tracker_System\Question_Generation\models\sft_model_config.json"

# Test 1: 默认加载config，看 attn_implementation
config1 = AutoConfig.from_pretrained(config_path)
print("Test 1 - Default config:")
print("  _attn_implementation:", getattr(config1, "_attn_implementation", "not set"))

# Test 2: 传 attn_implementation=eager 加载config
config2 = AutoConfig.from_pretrained(config_path, attn_implementation="eager")
print("Test 2 - With attn_implementation=eager:")
print("  _attn_implementation:", getattr(config2, "_attn_implementation", "not set"))

# Test 3: 直接看 transformers 的 _check_and_adjust_attn_implementation 行为
from transformers.modeling_utils import PreTrainedModel
print("\nTest 3 - Simulating what from_pretrained does:")

# 不传 attn_implementation
try:
    config1._attn_implementation = "flash_attention_2"
    # 模拟 _check_and_adjust_attn_implementation
    from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS
    print("  Available attention functions:", list(ALL_ATTENTION_FUNCTIONS.keys()))
except Exception as e:
    print(f"  Error: {e}")

# 传了 attn_implementation="eager" 后
config2._attn_implementation = "eager"
print("  config2._attn_implementation set to:", config2._attn_implementation)
print("  This should skip flash_attn import entirely")

print("\nDone!")
