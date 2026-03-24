"""Клавиатуры для Telegram бота."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Any


def create_action_keyboard(
    choices: List[Dict[str, Any]],
    available_locations: List[str] = None
) -> InlineKeyboardMarkup:
    """Создать клавиатуру с вариантами действий."""
    buttons = []
    
    # Основные действия из LLM
    for choice in choices[:5]:  # Максимум 5 основных действий
        label = choice.get("label", choice.get("verb", "Действие"))
        verb = choice.get("verb", choice.get("id", ""))
        
        # Добавляем подсказки
        hints = []
        if choice.get("cost_hint"):
            hints.append(choice["cost_hint"])
        if choice.get("risk_hint"):
            hints.append(choice["risk_hint"])
        
        if hints:
            label += f" ({', '.join(hints)})"
        
        buttons.append([InlineKeyboardButton(label, callback_data=f"action:{verb}")])
    
    # Кнопки перемещения (если есть доступные локации)
    if available_locations and len(available_locations) > 0:
        location_names = {
            "forest": "🌲 Лес",
            "river": "🌊 Река",
            "abandoned_house": "🏚️ Дом",
            "cave": "🕳️ Пещера",
            "road": "🛣️ Дорога",
            "clearing": "🌿 Поляна",
            "ruins": "🏛️ Руины",
            "swamp": "🐸 Болото"
        }
        
        # Показываем до 3 локаций в одной строке
        move_buttons = []
        for loc_id in available_locations[:3]:
            name = location_names.get(loc_id, loc_id)
            move_buttons.append(InlineKeyboardButton(name, callback_data=f"move:{loc_id}"))
        
        if move_buttons:
            buttons.append(move_buttons)
        
        # Если локаций больше 3, добавляем остальные
        if len(available_locations) > 3:
            more_buttons = []
            for loc_id in available_locations[3:6]:
                name = location_names.get(loc_id, loc_id)
                more_buttons.append(InlineKeyboardButton(name, callback_data=f"move:{loc_id}"))
            if more_buttons:
                buttons.append(more_buttons)
    
    # Дополнительные кнопки
    buttons.append([
        InlineKeyboardButton("📦 Инвентарь", callback_data="action:inventory"),
        InlineKeyboardButton("🗺️ Карта", callback_data="action:map"),
        InlineKeyboardButton("💾 Сохранить", callback_data="action:save")
    ])
    
    return InlineKeyboardMarkup(buttons)


def create_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Создать главное меню."""
    buttons = [
        [InlineKeyboardButton("🆕 Новая игра", callback_data="menu:new")],
        [InlineKeyboardButton("📂 Загрузить", callback_data="menu:load")],
        [InlineKeyboardButton("❓ Помощь", callback_data="menu:help")]
    ]
    return InlineKeyboardMarkup(buttons)


def create_craft_keyboard(available_recipes: List[str]) -> InlineKeyboardMarkup:
    """Создать клавиатуру для крафта."""
    buttons = []
    
    recipe_names = {
        "bandage": "Бинт",
        "torch": "Факел",
        "trap": "Ловушка",
        "water_filter": "Фильтр для воды"
    }
    
    for recipe_id in available_recipes:
        name = recipe_names.get(recipe_id, recipe_id)
        buttons.append([InlineKeyboardButton(name, callback_data=f"craft:{recipe_id}")])
    
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="action:back")])
    
    return InlineKeyboardMarkup(buttons)


def create_consume_keyboard(items: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Создать клавиатуру для использования предметов."""
    buttons = []
    
    consumable_items = [item for item in items if item.get("consumable", False)]
    
    for item in consumable_items[:10]:  # Максимум 10
        item_id = item.get("id", "")
        name = item.get("name", item_id)
        quantity = item.get("quantity", 0)
        
        if quantity > 0:
            buttons.append([
                InlineKeyboardButton(
                    f"{name} x{quantity}",
                    callback_data=f"consume:{item_id}"
                )
            ])
    
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="action:back")])
    
    return InlineKeyboardMarkup(buttons)


def create_move_keyboard(available_locations: List[str]) -> InlineKeyboardMarkup:
    """Создать клавиатуру для перемещения."""
    buttons = []
    
    location_names = {
        "forest": "🌲 Лес",
        "river": "🌊 Река",
        "abandoned_house": "🏚️ Заброшенный дом",
        "cave": "🕳️ Пещера",
        "road": "🛣️ Дорога",
        "clearing": "🌿 Поляна",
        "ruins": "🏛️ Руины",
        "swamp": "🐸 Болото"
    }
    
    for loc_id in available_locations:
        name = location_names.get(loc_id, loc_id)
        buttons.append([InlineKeyboardButton(name, callback_data=f"move:{loc_id}")])
    
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="action:back")])
    
    return InlineKeyboardMarkup(buttons)
