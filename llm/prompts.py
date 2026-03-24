"""Шаблоны промптов для LLM на русском языке."""

from typing import Dict, Any, List
from engine.state import GameState, PlayerState, WorldState


def build_scene_prompt(game_state: GameState, available_actions: List[str]) -> str:
    """Построить промпт для генерации сцены."""
    from engine.actions import action_handler
    
    player = game_state.player
    world = game_state.world
    
    # Получаем информацию о локации
    location = action_handler.locations.get(world.location, {})
    location_name = location.get("name", world.location)
    location_desc = location.get("description", "")
    gather_resources = location.get("gather_resources", [])
    connections = location.get("connections", [])
    danger_level = location.get("danger_level", 0)
    
    # Форматирование времени
    time_str = f"День {world.day}, {world.hour}:00"
    phase_names = {
        "morning": "утро",
        "day": "день",
        "evening": "вечер",
        "night": "ночь"
    }
    phase_str = phase_names.get(world.phase.value, world.phase.value)
    
    # Форматирование погоды
    weather_names = {
        "clear": "ясная погода",
        "rain": "дождь",
        "storm": "сильный шторм",
        "snow": "снег",
        "fog": "густой туман"
    }
    weather_str = weather_names.get(world.weather.value, world.weather.value)
    
    # Статус игрока
    status_parts = []
    if player.hp < 50:
        status_parts.append("ранен")
    if player.hunger > 70:
        status_parts.append("голоден")
    if player.thirst > 70:
        status_parts.append("испытываешь жажду")
    if player.warmth < 30:
        status_parts.append("замерзаешь")
    if player.energy < 30:
        status_parts.append("устал")
    if player.wet:
        status_parts.append("мокрый")
    if player.injury.value != "none":
        injury_names = {
            "bleeding": "кровотечение",
            "sprain": "растяжение",
            "infection": "инфекция"
        }
        status_parts.append(injury_names.get(player.injury.value, player.injury.value))
    
    status_str = ", ".join(status_parts) if status_parts else "в порядке"
    
    # Информация о ресурсах в локации
    resource_info = ""
    if gather_resources:
        resource_names = []
        for res_id in gather_resources:
            res_info = action_handler.items.get(res_id, {})
            resource_names.append(res_info.get("name", res_id))
        resource_info = f"В этой локации можно найти: {', '.join(resource_names)}."
    
    # Информация о соседних локациях
    connections_info = ""
    if connections:
        connection_names = []
        for conn_id in connections:
            conn_loc = action_handler.locations.get(conn_id, {})
            connection_names.append(conn_loc.get("name", conn_id))
        connections_info = f"Рядом находятся: {', '.join(connection_names)}."
    
    danger_levels = {
        0: "безопасная",
        1: "умеренно опасная",
        2: "опасная",
        3: "очень опасная"
    }
    danger_desc = danger_levels.get(danger_level, "неизвестная")
    
    prompt = f"""Ты - ведущий текстовой survival-игры в постапокалиптическом мире. Создавай атмосферные, детальные описания.

ТЕКУЩАЯ СИТУАЦИЯ:
- Время: {time_str}, {phase_str}
- Погода: {weather_str}
- Локация: {location_name} ({location_desc})
- Уровень опасности: {danger_desc}
- Состояние игрока: {status_str}
- Ресурсы: HP {player.hp}/100, Голод {player.hunger}/100, Жажда {player.thirst}/100, Тепло {player.warmth}/100, Энергия {player.energy}/100
{resource_info}
{connections_info}

ДОСТУПНЫЕ ДЕЙСТВИЯ: {', '.join(available_actions)}

ЗАДАЧА:
1. Опиши атмосферную сцену (3-5 предложений). Опиши что видит игрок, что слышит, какие запахи чувствует, какая атмосфера. Будь конкретным и детальным. Учитывай время суток, погоду, состояние игрока.
2. Предложи 4-5 вариантов действий из доступных. Каждое действие должно иметь:
   - Понятное название
   - Краткую подсказку о времени/риске (например: "2 часа, низкий риск" или "1 час, безопасно")

ВАЖНО: Верни ТОЛЬКО валидный JSON:
{{
  "scene_text": "детальное описание сцены (3-5 предложений)",
  "choices": [
    {{
      "id": "gather",
      "label": "Собрать ресурсы",
      "verb": "gather",
      "cost_hint": "2 часа",
      "risk_hint": "низкий риск"
    }}
  ],
  "tone": "мрачный/напряжённый/спокойный/тревожный"
}}

Используй ТОЛЬКО действия из списка: {', '.join(available_actions)}. Не выдумывай новые действия."""

    return prompt


def build_outcome_prompt(
    game_state: GameState,
    action: str,
    outcome: Dict[str, Any]
) -> str:
    """Построить промпт для озвучки результата действия."""
    player = game_state.player
    world = game_state.world
    
    success = outcome.get("success", False)
    message = outcome.get("message", "")
    resource_changes = outcome.get("resource_changes", {})
    items_gained = outcome.get("items_gained", [])
    items_lost = outcome.get("items_lost", [])
    event = outcome.get("event")
    
    # Названия действий
    action_names = {
        "look": "осмотреться",
        "gather": "собрать ресурсы",
        "hunt": "охотиться",
        "fire": "развести костёр",
        "shelter": "поставить укрытие",
        "consume": "употребить предмет",
        "rest": "отдохнуть",
        "craft": "создать предмет",
        "move": "переместиться"
    }
    action_name = action_names.get(action, action)
    
    # Описание изменений ресурсов
    resource_desc = []
    if "hp" in resource_changes:
        change = resource_changes["hp"]
        if change > 0:
            resource_desc.append(f"здоровье +{change}")
        elif change < 0:
            resource_desc.append(f"здоровье {change}")
    if "hunger" in resource_changes:
        change = resource_changes["hunger"]
        if change < 0:
            resource_desc.append(f"голод {change}")
    if "thirst" in resource_changes:
        change = resource_changes["thirst"]
        if change < 0:
            resource_desc.append(f"жажда {change}")
    if "warmth" in resource_changes:
        change = resource_changes["warmth"]
        if change > 0:
            resource_desc.append(f"тепло +{change}")
    
    # Формируем строки с информацией
    result_lines = [
        f"- Успех: {'да' if success else 'нет'}",
        f"- Системное сообщение: {message}"
    ]
    
    if resource_desc:
        result_lines.append(f"- Изменения: {', '.join(resource_desc)}")
    
    if items_gained:
        items_str = ', '.join([f"{item['id']} x{item.get('quantity', 1)}" for item in items_gained])
        result_lines.append(f"- Получено: {items_str}")
    
    if items_lost:
        result_lines.append(f"- Потеряно: {', '.join(items_lost)}")
    
    if event:
        result_lines.append(f"- Событие: {event.get('name', '')}")
    
    result_section = '\n'.join(result_lines)
    
    prompt = f"""Ты - ведущий текстовой survival-игры в постапокалиптическом мире. Игрок попытался {action_name}.

РЕЗУЛЬТАТ:
{result_section}

ТЕКУЩАЯ СИТУАЦИЯ:
- День {world.day}, {world.hour}:00
- Локация: {world.location}
- Погода: {world.weather.value}
- Состояние: HP {player.hp}/100, Голод {player.hunger}/100, Жажда {player.thirst}/100, Энергия {player.energy}/100

ЗАДАЧА:
Опиши результат действия художественным, атмосферным языком (2-4 предложения). Будь конкретным и детальным. Опиши:
- Что именно произошло
- Что почувствовал/увидел игрок
- Какие последствия это имело
- Атмосферу момента

ВАЖНО: Верни ТОЛЬКО текст описания, без JSON, без дополнительных комментариев. Пиши от второго лица ("ты", "тебе")."""

    return prompt


def get_action_labels() -> Dict[str, str]:
    """Получить русские названия действий."""
    return {
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
