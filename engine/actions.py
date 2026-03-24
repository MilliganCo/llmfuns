"""Обработка действий игрока."""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from engine.state import GameState, PlayerState, WorldState, InjuryType
from engine.balance import (
    calculate_action_success_chance,
    get_action_time,
    apply_passive_changes
)
from engine.events import event_manager
from config.settings import CONTENT_DIR, BALANCE


@dataclass
class ActionOutcome:
    """Результат действия."""
    success: bool
    message: str = ""
    time_spent: float = 0.0
    resource_changes: Dict[str, int] = None
    items_gained: List[Dict[str, Any]] = None
    items_lost: List[str] = None
    status_changes: Dict[str, Any] = None
    event: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.resource_changes is None:
            self.resource_changes = {}
        if self.items_gained is None:
            self.items_gained = []
        if self.items_lost is None:
            self.items_lost = []
        if self.status_changes is None:
            self.status_changes = {}


class ActionHandler:
    """Обработчик действий игрока."""
    
    def __init__(self):
        """Загрузить данные о локациях и предметах."""
        self.locations: Dict[str, Dict[str, Any]] = {}
        self.items: Dict[str, Dict[str, Any]] = {}
        self.recipes: Dict[str, Dict[str, Any]] = {}
        self._load_content()
    
    def _load_content(self):
        """Загрузить контент из JSON."""
        # Локации
        locations_path = CONTENT_DIR / "locations.json"
        with open(locations_path, "r", encoding="utf-8") as f:
            locations_data = json.load(f)
        self.locations = {loc["id"]: loc for loc in locations_data["locations"]}
        
        # Предметы
        items_path = CONTENT_DIR / "items.json"
        with open(items_path, "r", encoding="utf-8") as f:
            items_data = json.load(f)
        self.items = {item["id"]: item for item in items_data["items"]}
        
        # Рецепты
        recipes_path = CONTENT_DIR / "recipes.json"
        with open(recipes_path, "r", encoding="utf-8") as f:
            recipes_data = json.load(f)
        self.recipes = {recipe["id"]: recipe for recipe in recipes_data["recipes"]}
    
    def process_action(
        self,
        action: str,
        game_state: GameState,
        params: Optional[Dict[str, Any]] = None
    ) -> ActionOutcome:
        """Обработать действие игрока."""
        if params is None:
            params = {}
        
        # Применяем пассивные изменения перед действием
        time_spent = get_action_time(action)
        apply_passive_changes(game_state.player, game_state.world, time_spent)
        
        # Обработка конкретного действия
        handler_map = {
            "look": self._handle_look,
            "gather": self._handle_gather,
            "hunt": self._handle_hunt,
            "fire": self._handle_fire,
            "shelter": self._handle_shelter,
            "consume": self._handle_consume,
            "rest": self._handle_rest,
            "craft": self._handle_craft,
            "move": self._handle_move,
            "inventory": self._handle_inventory,
            "map": self._handle_map,
        }
        
        handler = handler_map.get(action)
        if not handler:
            return ActionOutcome(
                success=False,
                message=f"Неизвестное действие: {action}"
            )
        
        outcome = handler(game_state, params)
        outcome.time_spent = time_spent
        
        # Продвигаем время
        game_state.world.advance_time(time_spent)
        
        return outcome
    
    def _handle_look(self, game_state: GameState, params: Dict[str, Any]) -> ActionOutcome:
        """Осмотреться."""
        location = self.locations.get(game_state.world.location, {})
        location_name = location.get("name", game_state.world.location)
        description = location.get("description", "")
        gather_resources = location.get("gather_resources", [])
        connections = location.get("connections", [])
        danger_level = location.get("danger_level", 0)
        
        # Формируем информативное сообщение
        info_parts = [f"Ты находишься в {location_name.lower()}."]
        
        if description:
            info_parts.append(description)
        
        if gather_resources:
            resource_names = []
            for res_id in gather_resources:
                res_info = self.items.get(res_id, {})
                resource_names.append(res_info.get("name", res_id))
            info_parts.append(f"Здесь можно найти: {', '.join(resource_names)}.")
        
        if connections:
            connection_names = []
            for conn_id in connections:
                conn_loc = self.locations.get(conn_id, {})
                connection_names.append(conn_loc.get("name", conn_id))
            info_parts.append(f"Отсюда можно попасть в: {', '.join(connection_names)}.")
        
        danger_levels = {
            0: "безопасная",
            1: "умеренно опасная",
            2: "опасная",
            3: "очень опасная"
        }
        danger_desc = danger_levels.get(danger_level, "неизвестная")
        info_parts.append(f"Локация выглядит {danger_desc}.")
        
        message = " ".join(info_parts)
        
        return ActionOutcome(
            success=True,
            message=message,
            status_changes={"looked": True}  # Флаг для LLM
        )
    
    def _handle_gather(self, game_state: GameState, params: Dict[str, Any]) -> ActionOutcome:
        """Собрать ресурсы."""
        location = self.locations.get(game_state.world.location, {})
        gather_resources = location.get("gather_resources", [])
        
        if not gather_resources:
            return ActionOutcome(
                success=False,
                message="Здесь нечего собирать."
            )
        
        # Выбираем случайный ресурс
        resource_id = game_state.world.choice(gather_resources)
        resource_info = self.items.get(resource_id, {})
        
        # Шанс успеха
        chance = calculate_action_success_chance("gather", game_state.player, game_state.world)
        success = game_state.world.random() * 100 < chance
        
        if not success:
            return ActionOutcome(
                success=False,
                message="Тебе не удалось ничего найти."
            )
        
        # Количество (1-3)
        quantity = game_state.world.randint(1, 3)
        
        # Добавляем предмет
        game_state.player.add_item(
            resource_id,
            resource_info.get("name", resource_id),
            quantity,
            resource_info.get("weight", 0.0)
        )
        
        # Проверка на отравление (для грибов)
        poison = False
        if resource_id == "mushrooms" and resource_info.get("poison_chance", 0) > 0:
            if game_state.world.random() < resource_info["poison_chance"]:
                poison = True
                game_state.player.hp -= 10
                game_state.player.injury = InjuryType.INFECTION
        
        # Проверка на находку
        finding = event_manager.roll_finding(game_state.world, game_state.player, 0.1)
        
        outcome = ActionOutcome(
            success=True,
            message=f"Ты собрал {quantity} {resource_info.get('name', resource_id)}.",
            items_gained=[{"id": resource_id, "quantity": quantity}],
            event=finding
        )
        
        if poison:
            outcome.message += " Но что-то не так... ты чувствуешь себя плохо."
            outcome.status_changes["injury"] = "infection"
        
        return outcome
    
    def _handle_hunt(self, game_state: GameState, params: Dict[str, Any]) -> ActionOutcome:
        """Охота/рыбалка."""
        location = self.locations.get(game_state.world.location, {})
        
        if not location.get("hunt_available", False):
            return ActionOutcome(
                success=False,
                message="Здесь нельзя охотиться."
            )
        
        # Шанс успеха
        chance = calculate_action_success_chance("hunt", game_state.player, game_state.world)
        success = game_state.world.random() * 100 < chance
        
        if not success:
            return ActionOutcome(
                success=False,
                message="Охота не удалась."
            )
        
        # Получаем еду
        quantity = game_state.world.randint(1, 2)
        game_state.player.add_item("food", "Еда", quantity, 0.5)
        
        return ActionOutcome(
            success=True,
            message=f"Ты добыл {quantity} порцию еды.",
            items_gained=[{"id": "food", "quantity": quantity}]
        )
    
    def _handle_fire(self, game_state: GameState, params: Dict[str, Any]) -> ActionOutcome:
        """Развести костёр."""
        if not game_state.player.has_item("wood", 1):
            return ActionOutcome(
                success=False,
                message="Нужны дрова для костра."
            )
        
        chance = calculate_action_success_chance("fire", game_state.player, game_state.world)
        success = game_state.world.random() * 100 < chance
        
        if not success:
            return ActionOutcome(
                success=False,
                message="Не удалось развести костёр."
            )
        
        game_state.player.remove_item("wood", 1)
        game_state.player.warmth = min(100, game_state.player.warmth + 30)
        game_state.player.wet = False  # Просушивание
        
        return ActionOutcome(
            success=True,
            message="Ты развёл костёр. Стало теплее и суше.",
            items_lost=["wood"],
            resource_changes={"warmth": 30},
            status_changes={"wet": False}
        )
    
    def _handle_shelter(self, game_state: GameState, params: Dict[str, Any]) -> ActionOutcome:
        """Поставить укрытие."""
        if not (game_state.player.has_item("wood", 2) and game_state.player.has_item("cloth", 1)):
            return ActionOutcome(
                success=False,
                message="Нужны дрова (2) и ткань (1) для укрытия."
            )
        
        chance = calculate_action_success_chance("shelter", game_state.player, game_state.world)
        success = game_state.world.random() * 100 < chance
        
        if not success:
            return ActionOutcome(
                success=False,
                message="Не удалось поставить укрытие."
            )
        
        game_state.player.remove_item("wood", 2)
        game_state.player.remove_item("cloth", 1)
        
        return ActionOutcome(
            success=True,
            message="Ты поставил укрытие. Оно защитит от непогоды.",
            items_lost=["wood", "cloth"]
        )
    
    def _handle_consume(self, game_state: GameState, params: Dict[str, Any]) -> ActionOutcome:
        """Пить/есть."""
        item_id = params.get("item_id")
        if not item_id:
            return ActionOutcome(
                success=False,
                message="Укажи предмет для использования."
            )
        
        if not game_state.player.has_item(item_id, 1):
            return ActionOutcome(
                success=False,
                message="У тебя нет этого предмета."
            )
        
        item_info = self.items.get(item_id, {})
        if not item_info.get("consumable", False):
            return ActionOutcome(
                success=False,
                message="Это нельзя употребить."
            )
        
        game_state.player.remove_item(item_id, 1)
        
        # Применяем эффекты
        effects = item_info.get("effects", {})
        resource_changes = {}
        
        if "thirst" in effects:
            game_state.player.thirst += effects["thirst"]
            resource_changes["thirst"] = effects["thirst"]
        
        if "hunger" in effects:
            game_state.player.hunger += effects["hunger"]
            resource_changes["hunger"] = effects["hunger"]
        
        if "injury" in effects and effects["injury"] == "none":
            game_state.player.injury = InjuryType.NONE
            resource_changes["injury"] = "none"
        
        game_state.player.clamp_resources()
        
        return ActionOutcome(
            success=True,
            message=f"Ты использовал {item_info.get('name', item_id)}.",
            items_lost=[item_id],
            resource_changes=resource_changes
        )
    
    def _handle_rest(self, game_state: GameState, params: Dict[str, Any]) -> ActionOutcome:
        """Отдохнуть/поспать."""
        # Восстановление энергии
        energy_gain = 40 if game_state.world.is_night() else 20
        game_state.player.energy = min(100, game_state.player.energy + energy_gain)
        
        # Риск ночного события
        event = None
        if game_state.world.is_night():
            threat = event_manager.roll_threat(game_state.world, game_state.player, 0.15)
            if threat:
                event_manager.apply_event_effects(threat, game_state.player, game_state.world)
                event = threat
        
        return ActionOutcome(
            success=True,
            message="Ты отдохнул и восстановил силы.",
            resource_changes={"energy": energy_gain},
            event=event
        )
    
    def _handle_craft(self, game_state: GameState, params: Dict[str, Any]) -> ActionOutcome:
        """Крафт предметов."""
        recipe_id = params.get("recipe_id")
        if not recipe_id:
            return ActionOutcome(
                success=False,
                message="Укажи рецепт для крафта."
            )
        
        recipe = self.recipes.get(recipe_id)
        if not recipe:
            return ActionOutcome(
                success=False,
                message="Неизвестный рецепт."
            )
        
        # Проверка скилла
        skill_required = recipe.get("skill_required")
        skill_level = recipe.get("skill_level", 0)
        if skill_required and game_state.player.skills.get(skill_required, 0) < skill_level:
            return ActionOutcome(
                success=False,
                message=f"Нужен уровень {skill_required} {skill_level}."
            )
        
        # Проверка ингредиентов
        ingredients = recipe.get("ingredients", [])
        for ing in ingredients:
            if not game_state.player.has_item(ing["id"], ing.get("quantity", 1)):
                return ActionOutcome(
                    success=False,
                    message=f"Не хватает {ing['id']}."
                )
        
        # Шанс успеха
        chance = calculate_action_success_chance("craft", game_state.player, game_state.world)
        success = game_state.world.random() * 100 < chance
        
        if not success:
            return ActionOutcome(
                success=False,
                message="Крафт не удался."
            )
        
        # Тратим ингредиенты
        items_lost = []
        for ing in ingredients:
            game_state.player.remove_item(ing["id"], ing.get("quantity", 1))
            items_lost.append(ing["id"])
        
        # Создаём предмет
        result = recipe.get("result", {})
        result_id = result.get("id")
        result_quantity = result.get("quantity", 1)
        result_info = self.items.get(result_id, {})
        
        game_state.player.add_item(
            result_id,
            result_info.get("name", result_id),
            result_quantity,
            result_info.get("weight", 0.0)
        )
        
        return ActionOutcome(
            success=True,
            message=f"Ты создал {result_info.get('name', result_id)}.",
            items_gained=[{"id": result_id, "quantity": result_quantity}],
            items_lost=items_lost
        )
    
    def _handle_move(self, game_state: GameState, params: Dict[str, Any]) -> ActionOutcome:
        """Переместиться."""
        target_location = params.get("location")
        if not target_location:
            return ActionOutcome(
                success=False,
                message="Укажи локацию для перемещения."
            )
        
        current_loc = self.locations.get(game_state.world.location, {})
        connections = current_loc.get("connections", [])
        
        if target_location not in connections:
            return ActionOutcome(
                success=False,
                message="Нельзя переместиться туда отсюда."
            )
        
        chance = calculate_action_success_chance("move", game_state.player, game_state.world)
        success = game_state.world.random() * 100 < chance
        
        if not success:
            return ActionOutcome(
                success=False,
                message="Не удалось переместиться."
            )
        
        game_state.world.location = target_location
        
        # Риск угрозы при перемещении
        threat = event_manager.roll_threat(game_state.world, game_state.player, 0.1)
        
        return ActionOutcome(
            success=True,
            message=f"Ты переместился в {self.locations.get(target_location, {}).get('name', target_location)}.",
            event=threat
        )
    
    def _handle_inventory(self, game_state: GameState, params: Dict[str, Any]) -> ActionOutcome:
        """Показать инвентарь."""
        return ActionOutcome(
            success=True,
            message="Показываю инвентарь."
        )
    
    def _handle_map(self, game_state: GameState, params: Dict[str, Any]) -> ActionOutcome:
        """Показать карту."""
        return ActionOutcome(
            success=True,
            message="Показываю карту."
        )


# Глобальный экземпляр обработчика действий
action_handler = ActionHandler()
