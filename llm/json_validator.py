"""Валидация JSON-ответов от LLM."""

import json
import re
from typing import Dict, Any, List, Optional, Tuple


# Whitelist разрешённых действий
ALLOWED_VERBS = {
    "look", "gather", "hunt", "fire", "shelter",
    "consume", "rest", "craft", "move", "inventory", "map"
}


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Извлечь JSON из текста (может быть обёрнут в markdown или текст)."""
    # Пытаемся найти JSON блок
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Пытаемся найти код блок с JSON
    code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Пытаемся распарсить весь текст как JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    return None


def validate_scene_response(response_text: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Валидировать ответ LLM для сцены."""
    # Извлекаем JSON
    data = extract_json_from_text(response_text)
    
    if data is None:
        return False, None, "Не удалось извлечь JSON из ответа"
    
    # Проверяем обязательные поля
    if "scene_text" not in data:
        return False, None, "Отсутствует поле 'scene_text'"
    
    if "choices" not in data:
        return False, None, "Отсутствует поле 'choices'"
    
    if not isinstance(data["choices"], list):
        return False, None, "Поле 'choices' должно быть списком"
    
    if len(data["choices"]) == 0:
        return False, None, "Список 'choices' пуст"
    
    if len(data["choices"]) > 5:
        return False, None, "Слишком много вариантов (максимум 5)"
    
    # Валидируем каждый выбор
    validated_choices = []
    for i, choice in enumerate(data["choices"]):
        if not isinstance(choice, dict):
            continue
        
        # Проверяем verb
        verb = choice.get("verb") or choice.get("id")
        if not verb:
            continue
        
        if verb not in ALLOWED_VERBS:
            continue  # Пропускаем недопустимые действия
        
        validated_choice = {
            "id": choice.get("id", verb),
            "label": choice.get("label", verb),
            "verb": verb,
            "cost_hint": choice.get("cost_hint", ""),
            "risk_hint": choice.get("risk_hint", ""),
        }
        validated_choices.append(validated_choice)
    
    if len(validated_choices) == 0:
        return False, None, "Нет валидных вариантов действий"
    
    # Формируем валидированный ответ
    validated_data = {
        "scene_text": str(data["scene_text"]),
        "choices": validated_choices,
        "tone": data.get("tone", "neutral"),
    }
    
    return True, validated_data, "OK"


def get_fallback_choices(available_actions: List[str]) -> List[Dict[str, Any]]:
    """Получить стандартные варианты действий при ошибке валидации."""
    action_labels = {
        "look": "Осмотреться",
        "gather": "Собрать ресурсы",
        "hunt": "Охота/рыбалка",
        "fire": "Развести костёр",
        "shelter": "Поставить укрытие",
        "consume": "Пить/есть",
        "rest": "Отдохнуть/поспать",
        "craft": "Крафт",
        "move": "Переместиться",
        "inventory": "Инвентарь",
        "map": "Карта",
    }
    
    choices = []
    for action in available_actions[:5]:  # Максимум 5
        if action in action_labels:
            choices.append({
                "id": action,
                "label": action_labels[action],
                "verb": action,
                "cost_hint": "",
                "risk_hint": "",
            })
    
    return choices
