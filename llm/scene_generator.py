"""Генератор сцен с использованием LLM."""

from typing import Dict, Any, List
from engine.state import GameState
from llm.model import llm_model
from llm.prompts import build_scene_prompt
from llm.json_validator import validate_scene_response, get_fallback_choices
from config.settings import LLM_CONFIG


class SceneGenerator:
    """Генератор сцен для игры."""
    
    def __init__(self):
        """Инициализация генератора."""
        self.model = llm_model
    
    def generate_scene(
        self,
        game_state: GameState,
        available_actions: List[str]
    ) -> Dict[str, Any]:
        """Сгенерировать сцену с вариантами действий."""
        # Строим промпт
        prompt = build_scene_prompt(game_state, available_actions)
        
        # Генерируем ответ
        try:
            response_text = self.model.generate(
                prompt=prompt,
                max_new_tokens=LLM_CONFIG["max_new_tokens"],
                temperature=LLM_CONFIG["temperature"],
                top_p=LLM_CONFIG.get("top_p", 0.9)
            )
            
            # Валидируем ответ
            is_valid, validated_data, error_msg = validate_scene_response(response_text)
            
            if is_valid and validated_data:
                return validated_data
            
            # Фоллбек при ошибке валидации
            print(f"Ошибка валидации LLM ответа: {error_msg}")
            return self._get_fallback_scene(game_state, available_actions)
            
        except Exception as e:
            print(f"Ошибка генерации сцены: {e}")
            return self._get_fallback_scene(game_state, available_actions)
    
    def _get_fallback_scene(
        self,
        game_state: GameState,
        available_actions: List[str]
    ) -> Dict[str, Any]:
        """Получить стандартную сцену при ошибке."""
        world = game_state.world
        
        # Простое описание на основе состояния
        phase_names = {
            "morning": "утро",
            "day": "день",
            "evening": "вечер",
            "night": "ночь"
        }
        phase = phase_names.get(world.phase.value, world.phase.value)
        
        weather_names = {
            "clear": "ясная",
            "rain": "дождливая",
            "storm": "штормовая",
            "snow": "снежная",
            "fog": "туманная"
        }
        weather = weather_names.get(world.weather.value, world.weather.value)
        
        scene_text = f"День {world.day}, {phase}. Погода {weather}. Ты находишься в локации {world.location}."
        
        choices = get_fallback_choices(available_actions)
        
        return {
            "scene_text": scene_text,
            "choices": choices,
            "tone": "neutral",
        }


# Глобальный экземпляр генератора сцен
scene_generator = SceneGenerator()
