import asyncio
import logging
import sys
import os
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from config import BOT_TOKEN
from handlers import user
from services.database import Database
from utils.validators import validate_channel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Global database instance
db = None

async def set_bot_commands(bot: Bot):
    """Устанавливает команды бота для меню"""
    commands = [
        BotCommand(command="start", description="🚀 Начать расчет неустойки"),
        BotCommand(command="reset", description="🔄 Сбросить текущий расчет"),
        BotCommand(command="help", description="❓ Помощь и инструкции"),
        BotCommand(command="about", description="ℹ️ О боте"),
    ]
    
    # Команды для администраторов (будут видны только им)
    admin_commands = [
        BotCommand(command="admin", description="🔐 Админ панель"),
        BotCommand(command="stats", description="📊 Статистика бота"),
        BotCommand(command="adduser", description="➕ Добавить пользователя"),
        BotCommand(command="cancel", description="❌ Отменить текущее действие"),
    ]
    
    # Устанавливаем обычные команды для всех пользователей
    await bot.set_my_commands(commands)
    
    # Устанавливаем команды для администраторов
    for admin_id in user.ADMIN_IDS:
        await bot.set_my_commands(
            commands + admin_commands,
            scope={"type": "chat", "chat_id": admin_id}
        )

# Create bot instance
async def main():
    # Check if token is provided
    if not BOT_TOKEN:
        logging.critical("No token provided. Set the BOT_TOKEN environment variable.")
        return
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Initialize database
    global db
    db = Database()
    db.create_tables()
    
    # Initialize bot and dispatcher
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    
    # Устанавливаем команды бота
    await set_bot_commands(bot)
    
    # Проверка доступности канала и прав бота
    channel_valid, error = await validate_channel(bot, user.CHANNEL_ID)
    if not channel_valid:
        logging.critical(f"Channel configuration error: {error}")
        logging.warning("Bot will start, but subscription check might not work properly!")
    else:
        logging.info("Channel configuration is valid. Subscription check should work properly.")
    
    # Register routers
    dp.include_router(user.router)
    
    # Start polling
    logging.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
        # Close database connection
        if db:
            db.close()
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True) 
        # Close database connection
        if db:
            db.close() 