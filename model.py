"""
model.py — LLM 로드 및 추론
"""
import os

HF_CACHE_DIR = os.environ.get("HF_CACHE_DIR", "/opt/vessl/shared/hf-cache")
os.environ.setdefault("HF_HOME", HF_CACHE_DIR)
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", os.path.join(HF_CACHE_DIR, "hub"))

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

SUPPORTED_MODELS = {
    "0.5B": "Qwen/Qwen2.5-0.5B-Instruct",
    "3B":   "Qwen/Qwen2.5-3B-Instruct",
}


def load_model(size: str = "0.5B"):
    assert size in SUPPORTED_MODELS, f"size must be one of {list(SUPPORTED_MODELS)}"
    model_id = SUPPORTED_MODELS[size]
    print(f"Loading {model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=HF_CACHE_DIR)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        cache_dir=HF_CACHE_DIR,
        dtype=torch.float16,
        device_map="auto",
    )
    print(f"✅ {size} ready")
    return {"tokenizer": tokenizer, "model": model, "size": size}


def call_llm(bundle: dict, messages: list, max_new_tokens: int = 200) -> str:
    tok = bundle["tokenizer"]
    mdl = bundle["model"]
    text = tok.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tok([text], return_tensors="pt").to(mdl.device)
    with torch.no_grad():
        outputs = mdl.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tok.eos_token_id,
        )
    return tok.decode(
        outputs[0][inputs.input_ids.shape[1]:],
        skip_special_tokens=True,
    ).strip()
