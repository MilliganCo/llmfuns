"""Баланс игры - пассивные изменения ресурсов, модификаторы."""

from typing import Dict, Any
from engine.state import PlayerState, WorldState, WeatherType, TimePhase
from config.settings import BALANCE


def apply_passive_changes(player: PlayerState, world: WorldState, hours: float):
    """Применить пассивные изменения ресурсов за прошедшее время."""
    passive = BALANCE["passive_per_hour"]
    
    # Базовые изменения
    player.thirst += int(passive["thirst"] * hours)
    player.hunger += int(passive["hunger"] * hours)
    player.energy += int(passive["energy"] * hours)
    
    # Штрафы от погоды
    if world.weather in [WeatherType.RAIN, WeatherType.STORM]:
        weather_penalty = BALANCE["weather_penalties"].get(world.weather.value, {})
        if "warmth" in weather_penalty:
            player.warmth += int(weather_penalty["warmth"] * hours)
        
        # Шанс промокнуть
        if "wet_chance" in weather_penalty:
            if world.random() < weather_penalty["wet_chance"] * hours:
                player.wet = True
    
    # Критические эффекты
    thresholds = BALANCE["critical_thresholds"]
    critical_effects = BALANCE["critical_effects"]
    
    if player.thirst > thresholds["thirst"]:
        effect = critical_effects["thirst_critical"]
        player.hp += int(effect["hp_per_hour"] * hours)
    
    if player.warmth <= thresholds["warmth"]:
        effect = critical_effects["warmth_zero"]
        player.hp += int(effect["hp_per_hour"] * hours)
    
    # Ограничение ресурсов
    player.clamp_resources()


def calculate_action_success_chance(
    action: str,
    player: PlayerState,
    world: WorldState,
    location_bonus: int = 0
) -> float:
    """Рассчитать шанс успеха действия."""
    base_chance = BALANCE["action_base_chance"].get(action, 50)
    
    # Бонусы от скиллов
    skill_modifiers = BALANCE["skill_modifiers"]
    skill_bonus = 0
    
    if action == "gather":
        skill_bonus = player.skills.get("survival", 0) * skill_modifiers["survival"]
    elif action == "craft":
        skill_bonus = player.skills.get("craft", 0) * skill_modifiers["craft"]
    elif action == "hunt":
        skill_bonus = player.skills.get("survival", 0) * skill_modifiers["survival"]
    
    # Бонус от локации
    total_bonus = skill_bonus + location_bonus
    
    # Штрафы
    penalty_modifiers = BALANCE["penalty_modifiers"]
    total_penalty = 0
    
    if world.is_night():
        total_penalty += penalty_modifiers["night"]
    
    if world.weather == WeatherType.RAIN:
        total_penalty += penalty_modifiers["rain"]
    
    if player.wet:
        total_penalty += penalty_modifiers["wet"]
    
    if player.energy < BALANCE["critical_thresholds"]["energy"]:
        total_penalty += penalty_modifiers["low_energy"]
    
    if player.injury.value == "bleeding":
        total_penalty += penalty_modifiers["injury_bleeding"]
    elif player.injury.value == "sprain":
        total_penalty += penalty_modifiers["injury_sprain"]
    elif player.injury.value == "infection":
        total_penalty += penalty_modifiers["injury_infection"]
    
    # Итоговый шанс
    final_chance = base_chance + total_bonus + total_penalty
    return max(5, min(95, final_chance))  # Ограничение 5-95%


def get_action_time(action: str) -> float:
    """Получить время выполнения действия в часах."""
    return BALANCE["action_time"].get(action, 1.0)


def check_critical_conditions(player: PlayerState) -> Dict[str, bool]:
    """Проверить критические условия."""
    thresholds = BALANCE["critical_thresholds"]
    return {
        "thirst_critical": player.thirst > thresholds["thirst"],
        "hunger_critical": player.hunger > thresholds["hunger"],
        "warmth_zero": player.warmth <= thresholds["warmth"],
        "energy_low": player.energy < thresholds["energy"],
    }
