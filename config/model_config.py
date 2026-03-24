"""Конфигурация AirLLM модели."""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Модель
MODEL_ID: str = os.getenv("MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.1")

# Hugging Face токен (если модель gated)
HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")

# Пути для кэша и слоёв
HF_HOME: str = os.getenv("HF_HOME", "./hf_cache")
AIRLLM_LAYERS_PATH: str = os.getenv("AIRLLM_LAYERS_PATH", "./hf_airllm_layers")

# Ограничение VRAM (в GB)
VRAM_LIMIT_GB: float = float(os.getenv("VRAM_LIMIT_GB", "7.0"))

# Compression (4bit/8bit для экономии памяти)
COMPRESSION: Optional[str] = os.getenv("COMPRESSION", "4bit")  # None, "4bit", "8bit"

# Настройки AirLLM
AIRLLM_CONFIG = {
    "model_id": MODEL_ID,
    "hf_token": HF_TOKEN,
    "compression": COMPRESSION if COMPRESSION != "None" else None,
    "layer_shards_saving_path": AIRLLM_LAYERS_PATH,
    "profiling_mode": False,
    "prefetching": True,
}
