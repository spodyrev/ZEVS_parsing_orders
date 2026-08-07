"""
Основной модуль Telegram бота для отслеживания товаров на складе
"""
import sys
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)
from loguru import logger

# Добавляем путь к backend для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram_bot.config import get_settings
from telegram_bot.handlers import (
    photo_handler,
    text_handler,
    start_command,
    help_command,
)


async def error_handler(update: object, context) -> None:
    """
    Обработчик ошибок бота
    """
    logger.error(f"Exception while handling an update: {context.error}", exc_info=True)
    
    # Если есть update с сообщением, отправляем пользователю
    if isinstance(update, Update) and update.message:
        try:
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке вашего сообщения. "
                "Попробуйте еще раз или свяжитесь с администратором."
            )
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")


def create_application() -> Application:
    """
    Создать и настроить приложение бота
    
    Returns:
        Настроенное приложение Telegram бота
    """
    settings = get_settings()
    
    # Создаем приложение
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .build()
    )
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Регистрируем обработчики сообщений
    # Важно: фото обрабатываются отдельно от текста
    application.add_handler(
        MessageHandler(filters.PHOTO & ~filters.COMMAND, photo_handler)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)
    )
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)
    
    logger.info("Bot application created and configured")
    
    return application


async def start_bot() -> None:
    """
    Запустить бота в режиме polling
    
    Бот будет работать до получения сигнала остановки (Ctrl+C)
    """
    logger.info("Starting Telegram bot...")
    
    application = None
    try:
        # Создаем приложение
        application = create_application()
        
        # Инициализируем бота
        await application.initialize()
        await application.start()
        
        # Получаем информацию о боте
        bot = application.bot
        me = await bot.get_me()
        
        logger.info(f"Bot started successfully!")
        logger.info(f"Bot username: @{me.username}")
        logger.info(f"Bot name: {me.first_name}")
        logger.info(f"Bot ID: {me.id}")
        logger.info("Waiting for messages...")
        
        # Запускаем polling (получение обновлений)
        await application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=False,
        )
        
        # Ждем сигнала остановки (бесконечно)
        # Используем asyncio.Event который никогда не сработает
        # Остановка произойдет через KeyboardInterrupt
        import asyncio
        stop_event = asyncio.Event()
        await stop_event.wait()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)
        raise
    finally:
        if application:
            logger.info("Stopping bot...")
            if application.updater and application.updater.running:
                await application.updater.stop()
            await application.stop()
            await application.shutdown()
            logger.info("Bot stopped")


async def stop_bot(application: Application) -> None:
    """
    Остановить бота
    
    Args:
        application: Приложение бота для остановки
    """
    logger.info("Stopping bot gracefully...")
    
    try:
        if application.updater and application.updater.running:
            await application.updater.stop()
        
        await application.stop()
        await application.shutdown()
        
        logger.info("Bot stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping bot: {e}", exc_info=True)


if __name__ == "__main__":
    import asyncio
    
    # Настраиваем логирование
    logger.add(
        "logs/telegram_bot_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO",
    )
    
    # Запускаем бота
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
