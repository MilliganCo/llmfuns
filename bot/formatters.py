"""Форматирование сообщений для Telegram бота."""

from typing import List, Dict, Any
from engine.state import GameState, PlayerState, WorldState, Item
from engine.actions import action_handler
from config.settings import CONTENT_DIR
import json


class MessageFormatter:
    """Форматирование сообщений игры."""
    
    def __init__(self):
        """Инициализация форматтера."""
        pass
    
    def format_status(self, game_state: GameState) -> str:
        """Форматировать строку статуса игрока."""
        player = game_state.player
        world = game_state.world
        
        # Форматирование времени
        phase_names = {
            "morning": "🌅 Утро",
            "day": "☀️ День",
            "evening": "🌆 Вечер",
            "night": "🌙 Ночь"
        }
        phase = phase_names.get(world.phase.value, world.phase.value)
        
        # Форматирование погоды
        weather_icons = {
            "clear": "☀️",
            "rain": "🌧️",
            "storm": "⛈️",
            "snow": "❄️",
            "fog": "🌫️"
        }
        weather_icon = weather_icons.get(world.weather.value, "")
        weather_names = {
            "clear": "ясно",
            "rain": "дождь",
            "storm": "шторм",
            "snow": "снег",
            "fog": "туман"
        }
        weather_name = weather_names.get(world.weather.value, world.weather.value)
        
        # Прогресс-бары для ресурсов
        def progress_bar(value, max_val=100, length=10):
            filled = int(value / max_val * length)
            bar = "█" * filled + "░" * (length - filled)
            return bar
        
        status = f"""<b>📅 День {world.day} | {world.hour}:00 | {phase}</b>
{weather_icon} <b>{weather_name.capitalize()}</b> | 📍 <b>{self._get_location_name(world.location)}</b>

<b>💚 Здоровье:</b> {progress_bar(player.hp)} {player.hp}/100
<b>🍖 Голод:</b> {progress_bar(player.hunger)} {player.hunger}/100
<b>💧 Жажда:</b> {progress_bar(player.thirst)} {player.thirst}/100
<b>🔥 Тепло:</b> {progress_bar(player.warmth)} {player.warmth}/100
<b>⚡ Энергия:</b> {progress_bar(player.energy)} {player.energy}/100"""
        
        # Статусы
        status_parts = []
        if player.wet:
            status_parts.append("💧 Мокрый")
        if player.injury.value != "none":
            injury_names = {
                "bleeding": "🩸 Кровотечение",
                "sprain": "🦴 Растяжение",
                "infection": "🦠 Инфекция"
            }
            status_parts.append(injury_names.get(player.injury.value, player.injury.value))
        
        if status_parts:
            status += "\n\n<b>Статусы:</b> " + " | ".join(status_parts)
        
        return status
    
    def format_inventory(self, player: PlayerState) -> str:
        """Форматировать инвентарь."""
        if not player.inventory:
            return "<b>📦 Инвентарь пуст</b>"
        
        lines = ["<b>📦 Инвентарь:</b>\n"]
        total_weight = 0
        
        for item in player.inventory:
            weight = item.weight * item.quantity
            total_weight += weight
            lines.append(f"  • <b>{item.name}</b> x{item.quantity} ({weight:.1f} кг)")
        
        lines.append(f"\n<b>Общий вес:</b> {total_weight:.1f} кг")
        
        # Экипировка
        equipped = []
        for slot, item_id in player.equipment.items():
            if item_id:
                slot_names = {
                    "jacket": "Куртка",
                    "knife": "Нож",
                    "flask": "Фляга",
                    "flashlight": "Фонарь"
                }
                slot_name = slot_names.get(slot, slot)
                equipped.append(f"{slot_name}: {item_id}")
        
        if equipped:
            lines.append("\n<b>Экипировано:</b>")
            lines.extend(f"  • {eq}" for eq in equipped)
        
        return "\n".join(lines)
    
    def format_map(self, game_state: GameState) -> str:
        """Форматировать карту."""
        world = game_state.world
        current_loc = action_handler.locations.get(world.location, {})
        connections = current_loc.get("connections", [])
        
        lines = ["<b>🗺️ Карта:</b>\n"]
        lines.append(f"📍 <b>Текущая локация:</b> {self._get_location_name(world.location)}")
        
        if connections:
            lines.append("\n<b>Доступные локации:</b>")
            location_icons = {
                "forest": "🌲",
                "river": "🌊",
                "abandoned_house": "🏚️",
                "cave": "🕳️",
                "road": "🛣️",
                "clearing": "🌿",
                "ruins": "🏛️",
                "swamp": "🐸"
            }
            for conn_id in connections:
                conn_name = self._get_location_name(conn_id)
                icon = location_icons.get(conn_id, "📍")
                lines.append(f"  {icon} {conn_name}")
        
        return "\n".join(lines)
    
    def format_scene(
        self,
        game_state: GameState,
        scene_data: Dict[str, Any]
    ) -> str:
        """Форматировать сцену с описанием и вариантами."""
        status = self.format_status(game_state)
        scene_text = scene_data.get("scene_text", "")
        
        # Разделяем статус и описание сцены
        message = f"{status}\n\n<b>━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        message += f"<i>{scene_text}</i>"
        
        return message
    
    def format_outcome(
        self,
        game_state: GameState,
        narration: str
    ) -> str:
        """Форматировать результат действия."""
        status = self.format_status(game_state)
        
        message = f"{status}\n\n<b>━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        message += f"<i>{narration}</i>"
        
        return message
    
    def format_victory(self, game_state: GameState) -> str:
        """Форматировать сообщение о победе."""
        world = game_state.world
        
        if world.day > 7:
            return f"""<b>🎉 ПОБЕДА!</b>

Ты выжил <b>{world.day} дней</b> в этом суровом мире!

<b>Твои достижения:</b>
• Прожито дней: {world.day}
• Собрано сигнальных деталей: {game_state.player.get_item_quantity('signal_part')}
• Финальный HP: {game_state.player.hp}/100

Спасибо за игру!"""
        else:
            return f"""<b>🎉 ПОБЕДА!</b>

Ты собрал все сигнальные детали и выполнил свою миссию!

<b>Твои достижения:</b>
• Прожито дней: {world.day}
• Собрано сигнальных деталей: {game_state.player.get_item_quantity('signal_part')}
• Финальный HP: {game_state.player.hp}/100

Спасибо за игру!"""
    
    def format_defeat(self, game_state: GameState) -> str:
        """Форматировать сообщение о проигрыше."""
        world = game_state.world
        
        return f"""<b>💀 ПОРАЖЕНИЕ</b>

Ты не смог выжить в этом мире...

<b>Статистика:</b>
• Прожито дней: {world.day}
• Финальный HP: {game_state.player.hp}/100

Попробуй ещё раз!"""
    
    def _get_location_name(self, location_id: str) -> str:
        """Получить название локации."""
        location = action_handler.locations.get(location_id, {})
        return location.get("name", location_id)


# Глобальный экземпляр форматтера
formatter = MessageFormatter()
