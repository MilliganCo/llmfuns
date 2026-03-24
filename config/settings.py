"""Настройки игры и баланса."""

from pathlib import Path
from typing import Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

# Пути
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SAVES_DIR = DATA_DIR / "saves"
CONTENT_DIR = PROJECT_ROOT / "content"

# Создаём директории если их нет
SAVES_DIR.mkdir(parents=True, exist_ok=True)

# Баланс игры
BALANCE: Dict[str, Any] = {
    # Пассивные изменения ресурсов (за час)
    "passive_per_hour": {
        "thirst": 6,
        "hunger": 3,
        "energy": -2,
    },
    
    # Штрафы от погоды (за час)
    "weather_penalties": {
        "rain": {"warmth": -8, "wet_chance": 0.3},
        "storm": {"warmth": -12, "wet_chance": 0.6},
        "snow": {"warmth": -10},
        "fog": {},
    },
    
    # Критические пороги
    "critical_thresholds": {
        "thirst": 90,  # При жажде >90: HP -5/час
        "hunger": 90,  # При голоде >90: штраф к действиям
        "warmth": 0,   # При тепле 0: обморожение
        "energy": 20,  # При энергии <20: штраф к действиям
    },
    
    # Критические эффекты
    "critical_effects": {
        "thirst_critical": {"hp_per_hour": -5},
        "warmth_zero": {"hp_per_hour": -3},
    },
    
    # Базовые шансы успеха действий (%)
    "action_base_chance": {
        "gather": 55,
        "hunt": 40,
        "fire": 70,
        "shelter": 60,
        "craft": 65,
        "move": 80,
    },
    
    # Модификаторы от скиллов (бонус % за уровень)
    "skill_modifiers": {
        "survival": 5,  # +5% за уровень
        "craft": 8,
        "stealth": 10,
        "combat": 10,
    },
    
    # Штрафы к шансам успеха (%)
    "penalty_modifiers": {
        "night": -15,
        "rain": -10,
        "wet": -10,
        "low_energy": -15,  # энергия <20
        "injury_bleeding": -20,
        "injury_sprain": -15,
        "injury_infection": -25,
    },
    
    # Время действий (часы)
    "action_time": {
        "look": 0.5,
        "gather": 2,
        "hunt": 3,
        "fire": 1,
        "shelter": 2,
        "consume": 0.5,
        "rest": 4,
        "craft": 2,
        "move": 1,
    },
    
    # Условия победы
    "victory_conditions": {
        "survive_days": 7,
        "collect_signal_parts": 3,
    },
}

# Настройки LLM
LLM_CONFIG: Dict[str, Any] = {
    "max_new_tokens": 256,
    "max_context_length": 512,
    "temperature": 0.7,
    "top_p": 0.9,
}

# Настройки Telegram бота
TELEGRAM_CONFIG: Dict[str, Any] = {
    "token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "max_message_length": 4096,
}
