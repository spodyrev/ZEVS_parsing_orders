"""
Обработчики сообщений для Telegram бота
"""
import os
import sys
import shutil
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
import aiofiles

from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

# Добавляем путь к backend для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal
from models import Order
from telegram_bot.tracking_parser import TrackingNumberParser
from telegram_bot.config import get_settings


# Хранилище временных фото (message_id -> file_path)
# В продакшене лучше использовать Redis или другое хранилище
temp_photos: Dict[int, str] = {}

# Хранилище фото из медиа-группы (media_group_id -> [file_paths])
# Когда пользователь отправляет несколько фото одновременно
media_groups: Dict[str, List[str]] = {}

# Хранилище подписей медиа-групп (media_group_id -> caption)
media_group_captions: Dict[str, str] = {}

# Хранилище задач обработки медиа-групп (media_group_id -> Task)
# Для отложенной обработки после получения всех фото
media_group_tasks: Dict[str, asyncio.Task] = {}


async def process_media_group(media_group_id: str, message) -> None:
    """
    Обработать медиа-группу после сбора всех фото
    
    Вызывается через некоторое время после получения последнего фото в группе
    """
    try:
        # Ждем немного, чтобы убедиться что все фото получены
        await asyncio.sleep(2)
        
        if media_group_id not in media_groups:
            logger.warning(f"Media group {media_group_id} not found in storage")
            return
        
        photo_paths = media_groups[media_group_id]
        group_caption = media_group_captions.get(media_group_id, "")
        
        logger.info(f"Processing media group {media_group_id} with {len(photo_paths)} photos")
        
        if not group_caption:
            logger.warning(f"No caption found for media group {media_group_id}")
            # Удаляем из хранилища
            del media_groups[media_group_id]
            if media_group_id in media_group_captions:
                del media_group_captions[media_group_id]
            if media_group_id in media_group_tasks:
                del media_group_tasks[media_group_id]
            return
        
        tracking_numbers = TrackingNumberParser.extract_tracking_numbers(group_caption)
        
        if not tracking_numbers:
            logger.warning(f"No tracking numbers found in caption: {group_caption}")
            # Удаляем из хранилища
            del media_groups[media_group_id]
            del media_group_captions[media_group_id]
            if media_group_id in media_group_tasks:
                del media_group_tasks[media_group_id]
            return
        
        logger.info(f"Found {len(tracking_numbers)} tracking numbers: {tracking_numbers}")
        
        # Обрабатываем каждый трек-номер
        results = []
        for tracking_number in tracking_numbers:
            result = await process_tracking_number(
                tracking_number=tracking_number,
                photo_paths=photo_paths,
                message=message
            )
            results.append(result)
        
        # Формируем общий ответ
        success_count = sum(1 for r in results if r['success'])
        error_count = len(results) - success_count
        total_photos = sum(r.get('photos_count', 0) for r in results if r['success'])
        
        response = f"📦 Обработано номеров: {len(tracking_numbers)}\n"
        response += f"📸 Сохранено фото: {total_photos}\n"
        response += f"✅ Успешно: {success_count}\n"
        if error_count > 0:
            response += f"❌ Ошибок: {error_count}\n"
        
        response += "\n**Детали:**\n"
        for result in results:
            if result['success']:
                photos_info = f" ({result.get('photos_count', 0)} фото)" if result.get('photos_count', 0) > 1 else ""
                response += f"✅ {result['tracking_number']}: {result['order_id']}{photos_info}\n"
            else:
                response += f"❌ {result['tracking_number']}: {result['error']}\n"
        
        await message.reply_text(response, parse_mode='Markdown')
        
        # Удаляем временные файлы
        for photo_path in photo_paths:
            if os.path.exists(photo_path):
                os.remove(photo_path)
                logger.info(f"Removed temporary file: {photo_path}")
        
        # Очищаем медиа-группу из хранилища
        del media_groups[media_group_id]
        del media_group_captions[media_group_id]
        if media_group_id in media_group_tasks:
            del media_group_tasks[media_group_id]
        
    except asyncio.CancelledError:
        logger.info(f"Processing cancelled for media group {media_group_id}")
        raise
    except Exception as e:
        logger.error(f"Error processing media group {media_group_id}: {e}", exc_info=True)


async def process_tracking_number(tracking_number: str, photo_paths: List[str], message) -> dict:
    """
    Обработать трек-номер с фото (может быть несколько фото)
    
    Args:
        tracking_number: Трек-номер для поиска
        photo_paths: Список путей к временным файлам фото
        message: Telegram сообщение
        
    Returns:
        dict с результатом: {success: bool, tracking_number: str, order_id: str, error: str, photos_count: int}
    """
    db = SessionLocal()
    try:
        # Ищем заказ в БД
        order = db.query(Order).filter(
            Order.tracking_number == tracking_number
        ).first()
        
        if not order:
            # Пробуем найти без учета регистра
            order = db.query(Order).filter(
                Order.tracking_number.ilike(tracking_number)
            ).first()
        
        if not order:
            logger.warning(f"Order with tracking number {tracking_number} not found")
            return {
                'success': False,
                'tracking_number': tracking_number,
                'error': 'не найден в БД',
                'photos_count': 0
            }
        
        # Обновляем статус получения на складе
        order.received_at_warehouse = 1
        order.updated_at = datetime.now()
        
        # Сохраняем все фото
        settings = get_settings()
        photos_dir = settings.get_photos_path()
        saved_photos = []
        
        for idx, photo_path in enumerate(photo_paths):
            if not os.path.exists(photo_path):
                continue
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Добавляем индекс если фото несколько
            suffix = f"_{idx+1}" if len(photo_paths) > 1 else ""
            final_filename = f"{tracking_number}_{timestamp}{suffix}.jpg"
            final_filepath = photos_dir / final_filename
            
            # Копируем файл
            shutil.copy2(photo_path, final_filepath)
            saved_photos.append(final_filename)
            logger.info(f"Photo copied to: {final_filepath}")
        
        # Получаем существующие фото
        existing_photos = []
        if order.warehouse_photo_path:
            try:
                if order.warehouse_photo_path.startswith('['):
                    existing_photos = json.loads(order.warehouse_photo_path)
                else:
                    existing_photos = [order.warehouse_photo_path]
            except:
                existing_photos = [order.warehouse_photo_path]
        
        # Добавляем новые фото к существующим
        all_photos = existing_photos + saved_photos
        
        # Сохраняем как JSON массив
        order.warehouse_photo_path = json.dumps(all_photos)
        
        # Сохраняем изменения в БД
        db.commit()
        
        logger.info(f"Order {order.order_id} marked as received at warehouse with {len(saved_photos)} photos")
        
        return {
            'success': True,
            'tracking_number': tracking_number,
            'order_id': order.order_id,
            'photos_count': len(saved_photos)
        }
        
    except Exception as e:
        logger.error(f"Error processing tracking number {tracking_number}: {e}", exc_info=True)
        return {
            'success': False,
            'tracking_number': tracking_number,
            'error': str(e),
            'photos_count': 0
        }
    finally:
        db.close()


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик получения фотографий от склада
    
    Если фото с подписью - обрабатывает сразу
    Если без подписи - сохраняет временно до получения трек-номера
    """
    try:
        if not update.message or not update.message.photo:
            return
        
        message = update.message
        chat_id = message.chat_id
        caption = message.caption or ""
        
        logger.info(f"Received photo from chat {chat_id}, message_id: {message.message_id}, caption: {caption[:100]}")
        
        # Получаем фото наилучшего качества (последнее в списке)
        photo = message.photo[-1]
        
        # Скачиваем фото
        photo_file = await photo.get_file()
        
        # Создаем директорию для фото если не существует
        settings = get_settings()
        photos_dir = settings.get_photos_path()
        photos_dir.mkdir(exist_ok=True)
        
        # Временное имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_filename = f"temp_{message.message_id}_{timestamp}.jpg"
        temp_filepath = photos_dir / temp_filename
        
        # Сохраняем фото
        await photo_file.download_to_drive(str(temp_filepath))
        
        logger.info(f"Photo saved temporarily: {temp_filepath}")
        
        # Проверяем, это часть медиа-группы (несколько фото)
        media_group_id = message.media_group_id
        
        if media_group_id:
            # Это медиа-группа - сохраняем фото
            if media_group_id not in media_groups:
                media_groups[media_group_id] = []
            media_groups[media_group_id].append(str(temp_filepath))
            
            # Сохраняем подпись (обычно только у первого фото в группе)
            if caption and media_group_id not in media_group_captions:
                media_group_captions[media_group_id] = caption
            
            logger.info(f"Media group {media_group_id}: added photo {len(media_groups[media_group_id])}, caption: {bool(caption)}")
            
            # Отменяем предыдущую задачу обработки для этой группы если она есть
            if media_group_id in media_group_tasks:
                media_group_tasks[media_group_id].cancel()
                logger.info(f"Cancelled previous processing task for media group {media_group_id}")
            
            # Создаем новую задачу обработки с задержкой
            # Задержка позволяет собрать все фото группы
            task = asyncio.create_task(process_media_group(media_group_id, message))
            media_group_tasks[media_group_id] = task
            
            logger.info(f"Scheduled processing for media group {media_group_id} after delay")
            
            # Выходим, обработка произойдет автоматически через задачу
            return
        
        # Это одиночное фото (не медиа-группа)
        # Проверяем, есть ли трек-номер в подписи
        if caption:
            tracking_numbers = TrackingNumberParser.extract_tracking_numbers(caption)
            
            if tracking_numbers:
                logger.info(f"Found {len(tracking_numbers)} tracking numbers in photo caption: {tracking_numbers}")
                
                # Обрабатываем каждый трек-номер (с одним фото)
                results = []
                for tracking_number in tracking_numbers:
                    result = await process_tracking_number(
                        tracking_number=tracking_number,
                        photo_paths=[str(temp_filepath)],
                        message=message
                    )
                    results.append(result)
                
                # Формируем общий ответ
                success_count = sum(1 for r in results if r['success'])
                error_count = len(results) - success_count
                
                response = f"📦 Обработано номеров: {len(tracking_numbers)}\n"
                response += f"✅ Успешно: {success_count}\n"
                if error_count > 0:
                    response += f"❌ Ошибок: {error_count}\n"
                
                response += "\n**Детали:**\n"
                for result in results:
                    if result['success']:
                        response += f"✅ {result['tracking_number']}: {result['order_id']}\n"
                    else:
                        response += f"❌ {result['tracking_number']}: {result['error']}\n"
                
                await message.reply_text(response, parse_mode='Markdown')
                
                # Удаляем временный файл если все обработано
                if success_count > 0 and os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
                    logger.info(f"Removed temporary file: {temp_filepath}")
                
                return
        
        # Если трек-номера в подписи нет - сохраняем для последующей обработки
        temp_photos[message.message_id] = str(temp_filepath)
        
        # Отправляем подтверждение
        await message.reply_text(
            "📸 Фото получено! Теперь отправьте трек-номер товара."
        )
        
    except Exception as e:
        logger.error(f"Error handling photo: {e}", exc_info=True)
        if update.message:
            await update.message.reply_text(
                f"❌ Ошибка при обработке фото: {str(e)}"
            )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик текстовых сообщений с трек-номерами
    
    Извлекает трек-номер, ищет заказ в БД и обновляет статус
    """
    try:
        if not update.message or not update.message.text:
            return
        
        message = update.message
        text = message.text.strip()
        chat_id = message.chat_id
        
        logger.info(f"Received text from chat {chat_id}: {text}")
        
        # Пропускаем команды бота
        if text.startswith('/'):
            return
        
        # Извлекаем трек-номер
        tracking_number = TrackingNumberParser.extract_first_tracking_number(text)
        
        if not tracking_number:
            await message.reply_text(
                "⚠️ Не удалось распознать трек-номер в сообщении.\n"
                "Отправьте номер отслеживания (например: 79023797293946)"
            )
            return
        
        logger.info(f"Extracted tracking number: {tracking_number}")
        
        # Ищем заказ в БД
        db = SessionLocal()
        try:
            order = db.query(Order).filter(
                Order.tracking_number == tracking_number
            ).first()
            
            if not order:
                # Пробуем найти без учета регистра
                order = db.query(Order).filter(
                    Order.tracking_number.ilike(tracking_number)
                ).first()
            
            if not order:
                logger.warning(f"Order with tracking number {tracking_number} not found")
                
                await message.reply_text(
                    f"❌ Трек-номер `{tracking_number}` не найден в базе данных.\n\n"
                    "Возможные причины:\n"
                    "• Заказ еще не синхронизирован с Taobao\n"
                    "• Трек-номер указан неверно\n"
                    "• Заказ уже был отмечен как полученный\n\n"
                    "Проверьте номер и попробуйте снова.",
                    parse_mode='Markdown'
                )
                return
            
            # Обновляем статус получения на складе
            order.received_at_warehouse = 1
            order.updated_at = datetime.now()
            
            # Обрабатываем фото если есть
            photo_saved = False
            photo_path = None
            
            # Ищем последнее отправленное фото
            if temp_photos:
                # Берем последнее фото (по максимальному message_id)
                last_photo_msg_id = max(temp_photos.keys())
                temp_photo_path = temp_photos[last_photo_msg_id]
                
                if os.path.exists(temp_photo_path):
                    # Переименовываем фото
                    settings = get_settings()
                    photos_dir = settings.get_photos_path()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    final_filename = f"{tracking_number}_{timestamp}.jpg"
                    final_filepath = photos_dir / final_filename
                    
                    os.rename(temp_photo_path, final_filepath)
                    photo_path = str(final_filepath)
                    photo_saved = True
                    
                    # Сохраняем путь к фото в БД
                    order.warehouse_photo_path = final_filename  # Сохраняем только имя файла
                    
                    logger.info(f"Photo renamed to: {final_filepath}")
                    
                    # Удаляем из временного хранилища
                    del temp_photos[last_photo_msg_id]
            
            # Сохраняем изменения в БД
            db.commit()
            
            logger.info(f"Order {order.order_id} marked as received at warehouse")
            
            # Формируем сообщение с подтверждением
            response = (
                f"✅ **Товар отмечен как полученный на складе**\n\n"
                f"**Трек-номер:** `{tracking_number}`\n"
                f"**ID заказа:** `{order.order_id}`\n"
                f"**Описание:** {order.translated_description or order.description or 'Нет описания'}\n"
            )
            
            if photo_saved:
                response += f"**Фото:** Сохранено ({os.path.basename(photo_path)})\n"
            
            response += f"\n**Дата получения:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            await message.reply_text(response, parse_mode='Markdown')
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error handling text message: {e}", exc_info=True)
        if update.message:
            await update.message.reply_text(
                f"❌ Ошибка при обработке сообщения: {str(e)}"
            )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    welcome_message = (
        "👋 Привет! Я бот для отслеживания получения товаров на складе.\n\n"
        "**Как работать со мной:**\n"
        "1. Отправьте фото полученного товара 📸\n"
        "2. Отправьте трек-номер товара 📦\n"
        "3. Я найду заказ и отмечу его как полученный ✅\n\n"
        "**Формат трек-номера:**\n"
        "• Числовой: 79023797293946\n"
        "• China Post: LP123456789CN\n"
        "• SF Express: SF1234567890123\n\n"
        "Готов к работе! 🚀"
    )
    
    if update.message:
        await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_message = (
        "**Помощь по использованию бота**\n\n"
        "**Основной процесс:**\n"
        "1. 📸 Отправьте фото товара\n"
        "2. 📝 Отправьте трек-номер\n"
        "3. ✅ Получите подтверждение\n\n"
        "**Примеры трек-номеров:**\n"
        "• `79023797293946`\n"
        "• `LP123456789CN`\n"
        "• `SF1234567890123`\n\n"
        "**Команды:**\n"
        "/start - Начало работы\n"
        "/help - Эта справка\n\n"
        "**Что делать при ошибке:**\n"
        "• Проверьте правильность трек-номера\n"
        "• Убедитесь, что заказ синхронизирован с Taobao\n"
        "• Свяжитесь с администратором если проблема не решается\n"
    )
    
    if update.message:
        await update.message.reply_text(help_message, parse_mode='Markdown')
