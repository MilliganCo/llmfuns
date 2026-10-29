import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
from engine.state import GameState, Item


class SaveManagerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.save_dir = Path(self.temporary.name) / 'saves'
        settings = ModuleType('config.settings')
        settings.SAVES_DIR = self.save_dir
        config = ModuleType('config')
        config.__path__ = []
        config.settings = settings
        spec = importlib.util.spec_from_file_location('publication_save_manager', ROOT / 'save/manager.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'config': config, 'config.settings': settings}):
            spec.loader.exec_module(module)
        self.manager = module.save_manager

    def test_actual_game_state_roundtrip_and_delete(self):
        state = GameState()
        state.player.hp = 73
        state.player.inventory.append(Item(id='synthetic', name='Тестовый предмет', quantity=2))
        self.assertTrue(self.manager.save_game(42, state))
        self.assertTrue(self.manager.has_save(42))
        actual = self.manager.load_game(42)
        self.assertIsInstance(actual, GameState)
        self.assertEqual(actual.to_dict(), state.to_dict())
        self.assertEqual(json.loads((self.save_dir / '42.json').read_text('utf-8')), state.to_dict())
        self.assertTrue(self.manager.delete_save(42))
        self.assertFalse(self.manager.has_save(42))
        self.assertFalse(self.manager.delete_save(42))

    def test_missing_save_is_absent(self):
        self.assertFalse(self.manager.has_save(99))
        self.assertIsNone(self.manager.load_game(99))


if __name__ == '__main__':
    unittest.main()
