"""Обработчики команд и действий Telegram бота."""

from typing import Dict, Any
from telegram import Update
from telegram.ext import ContextTypes
from engine.state import GameState
from engine.actions import action_handler, ActionOutcome
from engine.events import event_manager
from llm.scene_generator import scene_generator
from llm.outcome_narrator import outcome_narrator
from bot.formatters import formatter
from bot.keyboard import (
    create_action_keyboard,
    create_main_menu_keyboard,
    create_craft_keyboard,
    create_consume_keyboard,
    create_move_keyboard
)
from save.manager import save_manager


# Хранилище активных игр (user_id -> GameState)
active_games: Dict[int, GameState] = {}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    await update.message.reply_text(
        "🎮 Добро пожаловать в Survival Game!\n\n"
        "Твоя цель - выжить 7 дней или собрать 3 сигнальные детали.\n\n"
        "Используй команды:\n"
        "/new - начать новую игру\n"
        "/load - загрузить сохранение\n"
        "/save - сохранить игру\n"
        "/help - помощь",
        reply_markup=create_main_menu_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help."""
    help_text = """📖 Помощь по игре:

🎯 Цель: Прожить 7 дней или собрать 3 сигнальные детали

📊 Ресурсы:
• HP - здоровье (0-100)
• Голод - растёт со временем
• Жажда - растёт быстрее голода
• Тепло - падает от холода/дождя
• Энергия - падает от действий

🎮 Действия:
• Осмотреться - получить информацию
• Собрать ресурсы - найти еду, воду, дрова
• Охота/рыбалка - добыть еду
• Развести костёр - согреться и просушиться
• Поставить укрытие - защита от непогоды
• Пить/есть - восстановить ресурсы
• Отдохнуть/поспать - восстановить энергию
• Крафт - создать предметы
• Переместиться - сменить локацию

💾 Сохранения:
• /save - сохранить игру
• /load - загрузить сохранение

Удачи в выживании!"""
    
    await update.message.reply_text(help_text)


async def new_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /new."""
    user_id = update.effective_user.id
    
    # Создаём новую игру
    game_state = GameState()
    active_games[user_id] = game_state
    
    # Генерируем первую сцену
    await send_scene(update, context, game_state)


async def load_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /load."""
    user_id = update.effective_user.id
    
    game_state = save_manager.load_game(user_id)
    
    if game_state is None:
        await update.message.reply_text(
            "❌ Сохранение не найдено. Используй /new для начала новой игры."
        )
        return
    
    active_games[user_id] = game_state
    await send_scene(update, context, game_state)


async def save_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /save."""
    user_id = update.effective_user.id
    
    game_state = active_games.get(user_id)
    
    if game_state is None:
        await update.message.reply_text(
            "❌ Нет активной игры. Используй /new для начала новой игры."
        )
        return
    
    success = save_manager.save_game(user_id, game_state)
    
    if success:
        await update.message.reply_text("✅ Игра сохранена!")
    else:
        await update.message.reply_text("❌ Ошибка сохранения.")


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback-запросов от кнопок."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    game_state = active_games.get(user_id)
    
    if game_state is None:
        await query.edit_message_text(
            "❌ Нет активной игры. Используй /new для начала новой игры."
        )
        return
    
    data = query.data
    
    # Обработка действий
    if data.startswith("action:"):
        action = data.split(":", 1)[1]
        await handle_action(update, context, game_state, action)
    
    # Обработка меню
    elif data.startswith("menu:"):
        menu_action = data.split(":", 1)[1]
        if menu_action == "new":
            await new_game_command(update, context)
        elif menu_action == "load":
            await load_game_command(update, context)
        elif menu_action == "help":
            await help_command(update, context)
    
    # Обработка крафта
    elif data.startswith("craft:"):
        recipe_id = data.split(":", 1)[1]
        await handle_craft(update, context, game_state, recipe_id)
    
    # Обработка использования предметов
    elif data.startswith("consume:"):
        item_id = data.split(":", 1)[1]
        await handle_consume(update, context, game_state, item_id)
    
    # Обработка перемещения
    elif data.startswith("move:"):
        location_id = data.split(":", 1)[1]
        await handle_move(update, context, game_state, location_id)
    
    # Назад
    elif data == "action:back":
        await send_scene(update, context, game_state)


async def handle_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    game_state: GameState,
    action: str
):
    """Обработать действие игрока."""
    user_id = update.effective_user.id
    
    # Специальные действия
    if action == "inventory":
        inventory_text = formatter.format_inventory(game_state.player)
        await update.callback_query.edit_message_text(inventory_text, parse_mode="HTML")
        await send_scene(update, context, game_state)
        return
    
    if action == "map":
        map_text = formatter.format_map(game_state)
        await update.callback_query.edit_message_text(map_text, parse_mode="HTML")
        await send_scene(update, context, game_state)
        return
    
    if action == "save":
        success = save_manager.save_game(user_id, game_state)
        if success:
            await update.callback_query.answer("✅ Игра сохранена!", show_alert=True)
        else:
            await update.callback_query.answer("❌ Ошибка сохранения", show_alert=True)
        return
    
    if action == "craft":
        # Показываем список рецептов
        available_recipes = list(action_handler.recipes.keys())
        keyboard = create_craft_keyboard(available_recipes)
        await update.callback_query.edit_message_text(
            "🔨 Выбери рецепт для крафта:",
            reply_markup=keyboard
        )
        return
    
    if action == "consume":
        # Показываем список предметов для использования
        items = [item.to_dict() for item in game_state.player.inventory]
        items_info = []
        for item in items:
            item_info = action_handler.items.get(item["id"], {})
            item_info["id"] = item["id"]
            item_info["name"] = item["name"]
            item_info["quantity"] = item["quantity"]
            items_info.append(item_info)
        
        keyboard = create_consume_keyboard(items_info)
        await update.callback_query.edit_message_text(
            "🍽️ Выбери предмет для использования:",
            reply_markup=keyboard
        )
        return
    
    if action == "move":
        # Показываем список доступных локаций
        current_loc = action_handler.locations.get(game_state.world.location, {})
        connections = current_loc.get("connections", [])
        keyboard = create_move_keyboard(connections)
        await update.callback_query.edit_message_text(
            "🚶 Выбери локацию для перемещения:",
            reply_markup=keyboard
        )
        return
    
    # Обычные действия (не требуют дополнительных параметров)
    outcome = action_handler.process_action(action, game_state, {})
    
    # Применяем эффекты события если есть
    if outcome.event:
        event_manager.apply_event_effects(outcome.event, game_state.player, game_state.world)
    
    # Проверяем условия победы/проигрыша
    if game_state.is_defeat():
        defeat_text = formatter.format_defeat(game_state)
        await update.callback_query.edit_message_text(defeat_text, parse_mode="HTML")
        del active_games[user_id]
        return
    
    if game_state.is_victory():
        victory_text = formatter.format_victory(game_state)
        await update.callback_query.edit_message_text(victory_text, parse_mode="HTML")
        del active_games[user_id]
        return
    
    # Озвучиваем результат
    narration = outcome_narrator.narrate_outcome(game_state, action, outcome)
    outcome_text = formatter.format_outcome(game_state, narration)
    
    await update.callback_query.edit_message_text(outcome_text, parse_mode="HTML")
    
    # Отправляем следующую сцену
    await send_scene(update, context, game_state)


async def handle_craft(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    game_state: GameState,
    recipe_id: str
):
    """Обработать крафт."""
    outcome = action_handler.process_action("craft", game_state, {"recipe_id": recipe_id})
    
    if outcome.success:
        narration = outcome_narrator.narrate_outcome(game_state, "craft", outcome)
        outcome_text = formatter.format_outcome(game_state, narration)
        await update.callback_query.edit_message_text(outcome_text)
    else:
        await update.callback_query.edit_message_text(
            f"❌ {outcome.message}",
            reply_markup=create_action_keyboard([])
        )
    
    await send_scene(update, context, game_state)


async def handle_consume(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    game_state: GameState,
    item_id: str
):
    """Обработать использование предмета."""
    outcome = action_handler.process_action("consume", game_state, {"item_id": item_id})
    
    if outcome.success:
        narration = outcome_narrator.narrate_outcome(game_state, "consume", outcome)
        outcome_text = formatter.format_outcome(game_state, narration)
        await update.callback_query.edit_message_text(outcome_text)
    else:
        await update.callback_query.edit_message_text(
            f"❌ {outcome.message}",
            reply_markup=create_action_keyboard([])
        )
    
    await send_scene(update, context, game_state)


async def handle_move(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    game_state: GameState,
    location_id: str
):
    """Обработать перемещение."""
    outcome = action_handler.process_action("move", game_state, {"location": location_id})
    
    if outcome.success:
        # Применяем эффекты события если есть
        if outcome.event:
            event_manager.apply_event_effects(outcome.event, game_state.player, game_state.world)
        
        narration = outcome_narrator.narrate_outcome(game_state, "move", outcome)
        outcome_text = formatter.format_outcome(game_state, narration)
        await update.callback_query.edit_message_text(outcome_text)
    else:
        await update.callback_query.edit_message_text(
            f"❌ {outcome.message}",
            reply_markup=create_action_keyboard([])
        )
    
    await send_scene(update, context, game_state)


async def send_scene(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    game_state: GameState
):
    """Отправить сцену игроку."""
    # Доступные действия (базовый набор)
    available_actions = [
        "look", "gather", "hunt", "fire", "shelter",
        "consume", "rest", "craft"
    ]
    
    # Получаем доступные локации для перемещения
    current_loc = action_handler.locations.get(game_state.world.location, {})
    available_locations = current_loc.get("connections", [])
    
    # Генерируем сцену
    scene_data = scene_generator.generate_scene(game_state, available_actions)
    
    # Форматируем сообщение
    scene_text = formatter.format_scene(game_state, scene_data)
    
    # Создаём клавиатуру с кнопками перемещения
    keyboard = create_action_keyboard(
        scene_data.get("choices", []),
        available_locations=available_locations
    )
    
    # Отправляем сообщение
    if update.callback_query:
        await update.callback_query.message.reply_text(
            scene_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            scene_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
