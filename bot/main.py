"""Главный файл Telegram бота."""

import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь поиска модулей
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from bot.handlers import (
    start_command,
    help_command,
    new_game_command,
    load_game_command,
    save_game_command,
    callback_handler
)
from config.settings import TELEGRAM_CONFIG

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Главная функция запуска бота."""
    token = TELEGRAM_CONFIG["token"]
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не установлен в .env файле!")
        return
    
    # Создаём приложение
    application = Application.builder().token(token).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("new", new_game_command))
    application.add_handler(CommandHandler("load", load_game_command))
    application.add_handler(CommandHandler("save", save_game_command))
    
    # Регистрируем обработчик callback-запросов
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    # Запускаем бота
    logger.info("Бот запущен!")
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("Бот остановлен.")


if __name__ == "__main__":
    main()
