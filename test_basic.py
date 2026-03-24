"""Базовый тест функциональности игры."""

from engine.state import GameState, PlayerState, WorldState
from engine.actions import action_handler
from engine.balance import apply_passive_changes, calculate_action_success_chance
from engine.events import event_manager
from save.manager import save_manager


def test_game_state():
    """Тест игрового состояния."""
    print("Тест 1: Создание игрового состояния...")
    game_state = GameState()
    assert game_state.player.hp == 100
    assert game_state.world.day == 1
    print("✓ Игровое состояние создано успешно")


def test_actions():
    """Тест действий."""
    print("\nТест 2: Обработка действий...")
    game_state = GameState()
    
    # Тест действия "look"
    outcome = action_handler.process_action("look", game_state, {})
    assert outcome.success
    print(f"✓ Действие 'look': {outcome.message}")
    
    # Тест действия "gather"
    outcome = action_handler.process_action("gather", game_state, {})
    print(f"✓ Действие 'gather': успех={outcome.success}, сообщение={outcome.message[:50]}...")


def test_balance():
    """Тест баланса."""
    print("\nТест 3: Баланс ресурсов...")
    game_state = GameState()
    
    initial_thirst = game_state.player.thirst
    apply_passive_changes(game_state.player, game_state.world, 1.0)  # 1 час
    
    assert game_state.player.thirst > initial_thirst
    print(f"✓ Пассивные изменения применены: жажда {initial_thirst} -> {game_state.player.thirst}")
    
    chance = calculate_action_success_chance("gather", game_state.player, game_state.world)
    assert 5 <= chance <= 95
    print(f"✓ Шанс успеха действия: {chance:.1f}%")


def test_events():
    """Тест событий."""
    print("\nТест 4: Система событий...")
    game_state = GameState()
    
    finding = event_manager.roll_finding(game_state.world, game_state.player, 1.0)  # 100% шанс
    if finding:
        print(f"✓ Найдено событие: {finding.get('name', 'неизвестно')}")
    else:
        print("✓ События не найдены (нормально при низком шансе)")


def test_save_load():
    """Тест сохранения/загрузки."""
    print("\nТест 5: Сохранение/загрузка...")
    game_state = GameState()
    game_state.player.hp = 75
    game_state.world.day = 3
    
    # Сохранение
    success = save_manager.save_game(999999, game_state)
    assert success
    print("✓ Игра сохранена")
    
    # Загрузка
    loaded_state = save_manager.load_game(999999)
    assert loaded_state is not None
    assert loaded_state.player.hp == 75
    assert loaded_state.world.day == 3
    print("✓ Игра загружена успешно")
    
    # Удаление тестового сохранения
    save_manager.delete_save(999999)
    print("✓ Тестовое сохранение удалено")


def test_victory_conditions():
    """Тест условий победы."""
    print("\nТест 6: Условия победы...")
    game_state = GameState()
    
    # Тест победы по дням
    game_state.world.day = 8
    assert game_state.is_victory()
    print("✓ Победа по дням работает")
    
    # Тест победы по сигнальным деталям
    game_state.world.day = 1
    game_state.player.add_item("signal_part", "Сигнальная деталь", 3, 0.5)
    assert game_state.is_victory()
    print("✓ Победа по сигнальным деталям работает")


def test_defeat_conditions():
    """Тест условий проигрыша."""
    print("\nТест 7: Условия проигрыша...")
    game_state = GameState()
    
    game_state.player.hp = 0
    assert game_state.is_defeat()
    print("✓ Проигрыш при HP=0 работает")


if __name__ == "__main__":
    print("=" * 50)
    print("Запуск базовых тестов игры")
    print("=" * 50)
    
    try:
        test_game_state()
        test_actions()
        test_balance()
        test_events()
        test_save_load()
        test_victory_conditions()
        test_defeat_conditions()
        
        print("\n" + "=" * 50)
        print("✓ Все тесты пройдены успешно!")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()
