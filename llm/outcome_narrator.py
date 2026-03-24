"""Озвучка результатов действий через LLM."""

from typing import Dict, Any
from engine.state import GameState
from engine.actions import ActionOutcome
from llm.model import llm_model
from llm.prompts import build_outcome_prompt
from config.settings import LLM_CONFIG


class OutcomeNarrator:
    """Озвучка результатов действий."""
    
    def __init__(self):
        """Инициализация нарратора."""
        self.model = llm_model
    
    def narrate_outcome(
        self,
        game_state: GameState,
        action: str,
        outcome: ActionOutcome
    ) -> str:
        """Озвучить результат действия."""
        # Преобразуем ActionOutcome в словарь
        outcome_dict = {
            "success": outcome.success,
            "message": outcome.message,
            "resource_changes": outcome.resource_changes,
            "items_gained": [
                {"id": item["id"], "quantity": item.get("quantity", 1)}
                for item in (outcome.items_gained or [])
            ],
            "items_lost": outcome.items_lost or [],
            "event": {
                "name": outcome.event.get("name"),
                "narrative_key": outcome.event.get("narrative_key")
            } if outcome.event else None,
        }
        
        # Строим промпт
        prompt = build_outcome_prompt(game_state, action, outcome_dict)
        
        # Генерируем ответ
        try:
            narration = self.model.generate(
                prompt=prompt,
                max_new_tokens=LLM_CONFIG["max_new_tokens"] // 2,  # Короче для результата
                temperature=LLM_CONFIG["temperature"],
                top_p=LLM_CONFIG.get("top_p", 0.9)
            )
            
            # Очищаем от лишнего
            narration = narration.strip()
            if narration.startswith('"') and narration.endswith('"'):
                narration = narration[1:-1]
            
            return narration if narration else outcome.message
            
        except Exception as e:
            print(f"Ошибка озвучки результата: {e}")
            # Фоллбек на системное сообщение
            return outcome.message


# Глобальный экземпляр нарратора
outcome_narrator = OutcomeNarrator()
