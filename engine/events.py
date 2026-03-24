"""Система событий - находки, угрозы, погодные события."""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from engine.state import WorldState, PlayerState, WeatherType, TimePhase
from config.settings import CONTENT_DIR


class EventManager:
    """Менеджер событий игры."""
    
    def __init__(self):
        """Загрузить события из JSON."""
        self.findings: List[Dict[str, Any]] = []
        self.threats: List[Dict[str, Any]] = []
        self.weather_events: List[Dict[str, Any]] = []
        self.lore: List[Dict[str, Any]] = []
        self._load_events()
    
    def _load_events(self):
        """Загрузить события из файла."""
        events_path = CONTENT_DIR / "events.json"
        with open(events_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.findings = data.get("findings", [])
        self.threats = data.get("threats", [])
        self.weather_events = data.get("weather_events", [])
        self.lore = data.get("lore", [])
    
    def _check_requirements(
        self,
        event: Dict[str, Any],
        world: WorldState,
        player: Optional[PlayerState] = None
    ) -> bool:
        """Проверить требования события."""
        requirements = event.get("requirements", {})
        
        # Проверка времени
        if "time" in requirements:
            time_req = requirements["time"]
            if isinstance(time_req, list):
                if world.phase.value not in time_req:
                    return False
            elif world.phase.value != time_req:
                return False
        
        # Проверка локации
        if "location" in requirements:
            loc_req = requirements["location"]
            if isinstance(loc_req, list):
                if world.location not in loc_req:
                    return False
            elif world.location != loc_req:
                return False
        
        # Проверка погоды
        if "weather" in requirements:
            weather_req = requirements["weather"]
            if isinstance(weather_req, list):
                if world.weather.value not in weather_req:
                    return False
            elif world.weather.value != weather_req:
                return False
        
        return True
    
    def _select_event(
        self,
        events: List[Dict[str, Any]],
        world: WorldState,
        player: Optional[PlayerState] = None
    ) -> Optional[Dict[str, Any]]:
        """Выбрать событие из списка с учётом весов и требований."""
        # Фильтруем по требованиям
        valid_events = [
            e for e in events
            if self._check_requirements(e, world, player)
        ]
        
        if not valid_events:
            return None
        
        # Взвешенный выбор
        total_weight = sum(e.get("weight", 1) for e in valid_events)
        if total_weight == 0:
            return None
        
        rand = world.random() * total_weight
        current_weight = 0
        
        for event in valid_events:
            current_weight += event.get("weight", 1)
            if rand <= current_weight:
                return event
        
        return valid_events[0] if valid_events else None
    
    def roll_finding(
        self,
        world: WorldState,
        player: PlayerState,
        base_chance: float = 0.15
    ) -> Optional[Dict[str, Any]]:
        """Проверить шанс находки."""
        if world.random() > base_chance:
            return None
        
        return self._select_event(self.findings, world, player)
    
    def roll_threat(
        self,
        world: WorldState,
        player: PlayerState,
        base_chance: float = 0.1
    ) -> Optional[Dict[str, Any]]:
        """Проверить шанс угрозы."""
        if world.random() > base_chance:
            return None
        
        return self._select_event(self.threats, world, player)
    
    def roll_weather_event(
        self,
        world: WorldState,
        base_chance: float = 0.2
    ) -> Optional[Dict[str, Any]]:
        """Проверить шанс погодного события."""
        if world.random() > base_chance:
            return None
        
        return self._select_event(self.weather_events, world)
    
    def roll_lore(
        self,
        world: WorldState,
        base_chance: float = 0.05
    ) -> Optional[Dict[str, Any]]:
        """Проверить шанс лор-события."""
        if world.random() > base_chance:
            return None
        
        return self._select_event(self.lore, world)
    
    def apply_event_effects(
        self,
        event: Dict[str, Any],
        player: PlayerState,
        world: WorldState
    ):
        """Применить эффекты события."""
        effects = event.get("effects", {})
        
        # Изменение HP
        if "hp" in effects:
            player.hp += effects["hp"]
        
        # Изменение ресурсов
        if "warmth" in effects:
            player.warmth += effects["warmth"]
        if "fear" in effects:
            player.fear += effects["fear"]
        
        # Травма
        if "injury" in effects:
            from engine.state import InjuryType
            player.injury = InjuryType(effects["injury"])
        
        # Статусы
        if "wet" in effects:
            player.wet = effects["wet"]
        
        # Предметы
        if "items" in effects:
            items_data = CONTENT_DIR / "items.json"
            with open(items_data, "r", encoding="utf-8") as f:
                items_info = json.load(f)
            
            items_dict = {item["id"]: item for item in items_info["items"]}
            
            for item_data in effects["items"]:
                item_id = item_data["id"]
                quantity = item_data.get("quantity", 1)
                item_info = items_dict.get(item_id, {})
                player.add_item(
                    item_id,
                    item_info.get("name", item_id),
                    quantity,
                    item_info.get("weight", 0.0)
                )
        
        # Бонусы (временные)
        if "hunt_bonus" in effects:
            # Сохраняем в событии для использования в действиях
            event["_temp_bonus"] = {"hunt": effects["hunt_bonus"]}
        
        player.clamp_resources()


# Глобальный экземпляр менеджера событий
event_manager = EventManager()
