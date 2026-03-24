"""Состояние игрока и мира."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import random


class InjuryType(Enum):
    """Типы травм."""
    NONE = "none"
    BLEEDING = "bleeding"
    SPRAIN = "sprain"
    INFECTION = "infection"


class WeatherType(Enum):
    """Типы погоды."""
    CLEAR = "clear"
    RAIN = "rain"
    STORM = "storm"
    SNOW = "snow"
    FOG = "fog"


class TimePhase(Enum):
    """Фазы времени суток."""
    MORNING = "morning"  # 6-12
    DAY = "day"  # 12-18
    EVENING = "evening"  # 18-22
    NIGHT = "night"  # 22-6


@dataclass
class Item:
    """Предмет в инвентаре."""
    id: str
    name: str
    quantity: int = 1
    weight: float = 0.0  # вес в кг
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        return {
            "id": self.id,
            "name": self.name,
            "quantity": self.quantity,
            "weight": self.weight,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Item":
        """Десериализация из словаря."""
        return cls(
            id=data["id"],
            name=data["name"],
            quantity=data.get("quantity", 1),
            weight=data.get("weight", 0.0),
        )


@dataclass
class PlayerState:
    """Состояние игрока."""
    # Ресурсы (0-100)
    hp: int = 100
    hunger: int = 50
    thirst: int = 50
    warmth: int = 80
    energy: int = 80
    
    # Инвентарь
    inventory: List[Item] = field(default_factory=list)
    
    # Экипировка (слоты)
    equipment: Dict[str, Optional[str]] = field(default_factory=lambda: {
        "jacket": None,
        "knife": None,
        "flask": None,
        "flashlight": None,
    })
    
    # Скиллы (0-3)
    skills: Dict[str, int] = field(default_factory=lambda: {
        "survival": 0,
        "craft": 0,
        "stealth": 0,
        "combat": 0,
    })
    
    # Статусы
    injury: InjuryType = InjuryType.NONE
    wet: bool = False
    fear: int = 0  # 0-100, опционально
    
    def clamp_resources(self):
        """Ограничить ресурсы в диапазоне 0-100."""
        self.hp = max(0, min(100, self.hp))
        self.hunger = max(0, min(100, self.hunger))
        self.thirst = max(0, min(100, self.thirst))
        self.warmth = max(0, min(100, self.warmth))
        self.energy = max(0, min(100, self.energy))
        self.fear = max(0, min(100, self.fear))
    
    def add_item(self, item_id: str, name: str, quantity: int = 1, weight: float = 0.0):
        """Добавить предмет в инвентарь."""
        # Проверяем, есть ли уже такой предмет
        for item in self.inventory:
            if item.id == item_id:
                item.quantity += quantity
                return
        
        # Добавляем новый предмет
        self.inventory.append(Item(id=item_id, name=name, quantity=quantity, weight=weight))
    
    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        """Удалить предмет из инвентаря."""
        for i, item in enumerate(self.inventory):
            if item.id == item_id:
                item.quantity -= quantity
                if item.quantity <= 0:
                    self.inventory.pop(i)
                return True
        return False
    
    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        """Проверить наличие предмета."""
        for item in self.inventory:
            if item.id == item_id and item.quantity >= quantity:
                return True
        return False
    
    def get_item_quantity(self, item_id: str) -> int:
        """Получить количество предмета."""
        for item in self.inventory:
            if item.id == item_id:
                return item.quantity
        return 0
    
    def get_total_weight(self) -> float:
        """Получить общий вес инвентаря."""
        return sum(item.weight * item.quantity for item in self.inventory)
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        return {
            "hp": self.hp,
            "hunger": self.hunger,
            "thirst": self.thirst,
            "warmth": self.warmth,
            "energy": self.energy,
            "inventory": [item.to_dict() for item in self.inventory],
            "equipment": self.equipment,
            "skills": self.skills,
            "injury": self.injury.value,
            "wet": self.wet,
            "fear": self.fear,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlayerState":
        """Десериализация из словаря."""
        player = cls(
            hp=data.get("hp", 100),
            hunger=data.get("hunger", 50),
            thirst=data.get("thirst", 50),
            warmth=data.get("warmth", 80),
            energy=data.get("energy", 80),
            equipment=data.get("equipment", {}),
            skills=data.get("skills", {}),
            injury=InjuryType(data.get("injury", "none")),
            wet=data.get("wet", False),
            fear=data.get("fear", 0),
        )
        player.inventory = [Item.from_dict(item_data) for item_data in data.get("inventory", [])]
        player.clamp_resources()
        return player


@dataclass
class WorldState:
    """Состояние мира."""
    # Время
    day: int = 1
    hour: int = 8  # 0-23
    phase: TimePhase = TimePhase.MORNING
    
    # Погода
    weather: WeatherType = WeatherType.CLEAR
    temperature: str = "moderate"  # cold, moderate, warm
    
    # Локация
    location: str = "forest"  # ID локации
    
    # Прогресс цели
    signal_parts: int = 0  # собрано сигнальных деталей
    
    # RNG seed для воспроизводимости
    rng_seed: Optional[int] = None
    _rng: random.Random = field(default_factory=random.Random, init=False)
    
    def __post_init__(self):
        """Инициализация RNG."""
        if self.rng_seed is not None:
            self._rng.seed(self.rng_seed)
        else:
            self.rng_seed = random.randint(1, 1000000)
            self._rng.seed(self.rng_seed)
    
    def update_phase(self):
        """Обновить фазу времени суток."""
        if 6 <= self.hour < 12:
            self.phase = TimePhase.MORNING
        elif 12 <= self.hour < 18:
            self.phase = TimePhase.DAY
        elif 18 <= self.hour < 22:
            self.phase = TimePhase.EVENING
        else:
            self.phase = TimePhase.NIGHT
    
    def advance_time(self, hours: float):
        """Продвинуть время вперёд."""
        self.hour += int(hours)
        
        # Переход через полночь
        while self.hour >= 24:
            self.hour -= 24
            self.day += 1
        
        self.update_phase()
    
    def is_night(self) -> bool:
        """Проверить, ночь ли сейчас."""
        return self.phase == TimePhase.NIGHT
    
    def random(self) -> float:
        """Получить случайное число от 0 до 1."""
        return self._rng.random()
    
    def randint(self, a: int, b: int) -> int:
        """Получить случайное целое число."""
        return self._rng.randint(a, b)
    
    def choice(self, seq):
        """Выбрать случайный элемент из последовательности."""
        return self._rng.choice(seq)
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        return {
            "day": self.day,
            "hour": self.hour,
            "phase": self.phase.value,
            "weather": self.weather.value,
            "temperature": self.temperature,
            "location": self.location,
            "signal_parts": self.signal_parts,
            "rng_seed": self.rng_seed,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldState":
        """Десериализация из словаря."""
        world = cls(
            day=data.get("day", 1),
            hour=data.get("hour", 8),
            phase=TimePhase(data.get("phase", "morning")),
            weather=WeatherType(data.get("weather", "clear")),
            temperature=data.get("temperature", "moderate"),
            location=data.get("location", "forest"),
            signal_parts=data.get("signal_parts", 0),
            rng_seed=data.get("rng_seed"),
        )
        world.update_phase()
        return world


@dataclass
class GameState:
    """Полное состояние игры."""
    player: PlayerState = field(default_factory=PlayerState)
    world: WorldState = field(default_factory=WorldState)
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        return {
            "player": self.player.to_dict(),
            "world": self.world.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameState":
        """Десериализация из словаря."""
        return cls(
            player=PlayerState.from_dict(data.get("player", {})),
            world=WorldState.from_dict(data.get("world", {})),
        )
    
    def is_victory(self) -> bool:
        """Проверить условие победы."""
        from config.settings import BALANCE
        victory = BALANCE["victory_conditions"]
        return (
            self.world.day > victory["survive_days"] or
            self.player.get_item_quantity("signal_part") >= victory["collect_signal_parts"]
        )
    
    def is_defeat(self) -> bool:
        """Проверить условие проигрыша."""
        return self.player.hp <= 0
