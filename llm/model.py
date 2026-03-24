"""Загрузка и управление моделью AirLLM."""

from __future__ import annotations

import torch
import os
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from airllm import AutoModel

from config.model_config import (
    AIRLLM_CONFIG,
    VRAM_LIMIT_GB,
    HF_HOME,
    AIRLLM_LAYERS_PATH
)


class LLMModel:
    """Обёртка для модели AirLLM."""
    
    _instance: Optional['LLMModel'] = None
    _model: Optional['AutoModel'] = None
    
    def __new__(cls):
        """Singleton паттерн."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Инициализация модели (ленивая загрузка)."""
        self._initialized = False
    
    def _ensure_initialized(self):
        """Убедиться, что модель инициализирована."""
        if not self._initialized and self._model is None:
            self._initialize_model()
            self._initialized = True
    
    def _initialize_model(self):
        """Инициализировать модель AirLLM."""
        # Ленивый импорт airllm
        try:
            from airllm import AutoModel
        except ImportError as e:
            raise ImportError(f"Не удалось импортировать airllm: {e}. Установите: pip install airllm")
        
        # Установка переменных окружения для кэша
        os.environ["HF_HOME"] = HF_HOME
        os.environ["TRANSFORMERS_CACHE"] = HF_HOME
        
        # Ограничение VRAM
        try:
            if torch.cuda.is_available():
                torch.cuda.init()
                props = torch.cuda.get_device_properties(0)
                total_gb = props.total_memory / (1024**3)
                
                fraction = min(VRAM_LIMIT_GB / total_gb, 0.95)
                torch.cuda.set_per_process_memory_fraction(fraction, 0)
                
                print(f"GPU total: {total_gb:.1f} GB, limit fraction: {fraction:.2f}")
        except Exception as e:
            print(f"Предупреждение: не удалось настроить CUDA: {e}")
            print("Бот будет работать без GPU (медленнее)")
        
        # Загрузка модели
        try:
            print(f"Загрузка модели {AIRLLM_CONFIG['model_id']}...")
            
            config = AIRLLM_CONFIG.copy()
            if config.get("layer_shards_saving_path"):
                os.makedirs(config["layer_shards_saving_path"], exist_ok=True)
            
            self._model = AutoModel.from_pretrained(
                config["model_id"],
                compression=config.get("compression"),
                layer_shards_saving_path=config.get("layer_shards_saving_path"),
                hf_token=config.get("hf_token"),
                profiling_mode=config.get("profiling_mode", False),
                prefetching=config.get("prefetching", True),
            )
            
            print("Модель загружена успешно!")
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            print("Бот будет работать без LLM, используя стандартные описания.")
            raise
    
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> str:
        """Сгенерировать текст из промпта."""
        self._ensure_initialized()
        if self._model is None:
            raise RuntimeError("Модель не инициализирована")
        
        # Токенизация
        tokens = self._model.tokenizer(
            [prompt],
            return_tensors="pt",
            return_attention_mask=False,
            truncation=True,
            max_length=512,
            padding=False,
        )
        
        # Генерация
        input_ids = tokens["input_ids"].cuda()
        
        output = self._model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            use_cache=True,
            return_dict_in_generate=True,
        )
        
        # Декодирование
        generated_text = self._model.tokenizer.decode(
            output.sequences[0],
            skip_special_tokens=True
        )
        
        # Убираем оригинальный промпт из результата
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):].strip()
        
        return generated_text
    
    @property
    def model(self) -> 'AutoModel':
        """Получить модель."""
        self._ensure_initialized()
        if self._model is None:
            raise RuntimeError("Модель не инициализирована")
        return self._model


# Глобальный экземпляр модели
llm_model = LLMModel()
