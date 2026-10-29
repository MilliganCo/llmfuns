"""Система сохранения и загрузки игры."""

import json
from pathlib import Path
from typing import Optional
from engine.state import GameState
from config.settings import SAVES_DIR


class SaveManager:
    """Менеджер сохранений игры."""

    def __init__(self):
        """Инициализация менеджера."""
        self.saves_dir = SAVES_DIR
        self.saves_dir.mkdir(parents=True, exist_ok=True)

    def save_game(self, user_id: int, game_state: GameState) -> bool:
        """Сохранить игру."""
        try:
            save_path = self.saves_dir / f"{user_id}.json"
            data = game_state.to_dict()

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False

    def load_game(self, user_id: int) -> Optional[GameState]:
        """Загрузить игру."""
        try:
            save_path = self.saves_dir / f"{user_id}.json"

            if not save_path.exists():
                return None

            with open(save_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            game_state = GameState.from_dict(data)
            return game_state
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return None

    def delete_save(self, user_id: int) -> bool:
        """Удалить сохранение."""
        try:
            save_path = self.saves_dir / f"{user_id}.json"
            if save_path.exists():
                save_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Ошибка удаления: {e}")
            return False

    def has_save(self, user_id: int) -> bool:
        """Проверить наличие сохранения."""
        save_path = self.saves_dir / f"{user_id}.json"
        return save_path.exists()


# Глобальный экземпляр менеджера сохранений
save_manager = SaveManager()
