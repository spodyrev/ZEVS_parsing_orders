"""
Модели базы данных
Описывают структуру таблиц
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from database import Base
from datetime import datetime
import json


class Order(Base):
    """
    Модель заказа с Taobao
    
    Каждый заказ - это одна строка в таблице 'orders'
    """
    __tablename__ = "orders"
    
    # Первичный ключ - уникальный ID в нашей БД
    id = Column(Integer, primary_key=True, index=True)
    
    # ID заказа на Taobao (уникальный)
    order_id = Column(String, unique=True, index=True, nullable=False)
    
    # Трек-номер отправления
    tracking_number = Column(String, nullable=True)
    
    # Статус заказа
    # Возможные значения: created, paid, shipped, delivered, cancelled
    status = Column(String, nullable=False, default="created")
    
    # Описание заказа (название товаров) - оригинал на китайском
    description = Column(Text, nullable=True)
    
    # Переведенное описание на русский язык (AI-перевод)
    translated_description = Column(Text, nullable=True)
    
    # URL товара на Taobao
    product_url = Column(String, nullable=True)
    
    # URL изображения товара
    product_image_url = Column(String, nullable=True)
    
    # Количество товаров в заказе
    items_count = Column(Integer, default=1)
    
    # Общая стоимость
    total_price = Column(Float, nullable=True)
    
    # Валюта
    currency = Column(String, default="CNY")
    
    # Дата создания заказа на Taobao
    order_date = Column(DateTime, nullable=True)
    
    # Когда заказ был добавлен в нашу БД
    created_at = Column(DateTime, server_default=func.now())
    
    # Последнее обновление информации
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Архивирован ли заказ
    archived = Column(Integer, default=0, nullable=False)  # 0 = активен, 1 = архивирован
    
    # Получен на складе
    received_at_warehouse = Column(Integer, default=0, nullable=False)  # 0 = нет, 1 = да
    
    # Удален ли заказ (в корзине)
    deleted_at = Column(DateTime, nullable=True)  # NULL = не удален, иначе = дата удаления
    
    # Пути к фото товара со склада (JSON массив)
    # Например: ["435301476185280_20260806_225130.jpg", "435301476185280_20260806_225131.jpg"]
    warehouse_photo_path = Column(String, nullable=True)
    
    # Полные сырые данные от Taobao (для отладки)
    raw_data = Column(JSON, nullable=True)
    
    def __repr__(self):
        """Красивое отображение заказа при печати"""
        return f"<Order {self.order_id}: {self.status}>"
    
    def to_dict(self):
        """
        Конвертирует заказ в словарь (для API)
        """
        # Парсим фото из JSON если это строка
        warehouse_photos = []
        if self.warehouse_photo_path:
            try:
                if self.warehouse_photo_path.startswith('['):
                    warehouse_photos = json.loads(self.warehouse_photo_path)
                else:
                    # Старый формат - одно фото
                    warehouse_photos = [self.warehouse_photo_path]
            except:
                warehouse_photos = [self.warehouse_photo_path]
        
        return {
            "id": self.id,
            "order_id": self.order_id,
            "tracking_number": self.tracking_number,
            "status": self.status,
            "description": self.description,
            "translated_description": self.translated_description,
            "product_url": self.product_url,
            "product_image_url": self.product_image_url,
            "items_count": self.items_count,
            "total_price": self.total_price,
            "currency": self.currency,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "archived": bool(self.archived),
            "received_at_warehouse": bool(self.received_at_warehouse),
            "warehouse_photo_path": self.warehouse_photo_path,  # Сырой JSON
            "warehouse_photos": warehouse_photos,  # Массив путей
        }


class User(Base):
    """
    Модель пользователя системы (сотрудника)
    
    Аутентификация через Telegram Login Widget
    """
    __tablename__ = "users"
    
    # Первичный ключ
    id = Column(Integer, primary_key=True, index=True)
    
    # Telegram ID пользователя (уникальный)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    
    # Номер телефона (для проверки доступа)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    
    # Имя пользователя из Telegram
    first_name = Column(String, nullable=True)
    
    # Фамилия пользователя из Telegram
    last_name = Column(String, nullable=True)
    
    # Username в Telegram (без @)
    username = Column(String, nullable=True)
    
    # URL фото профиля из Telegram
    photo_url = Column(String, nullable=True)
    
    # Является ли пользователь администратором
    is_admin = Column(Integer, default=0, nullable=False)  # 0 = обычный пользователь, 1 = админ
    
    # Активен ли пользователь
    is_active = Column(Integer, default=1, nullable=False)  # 0 = деактивирован, 1 = активен
    
    # Когда пользователь был создан
    created_at = Column(DateTime, server_default=func.now())
    
    # Последний вход в систему
    last_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        """Красивое отображение пользователя при печати"""
        return f"<User {self.telegram_id}: {self.first_name} {self.last_name}>"
    
    def to_dict(self):
        """
        Конвертирует пользователя в словарь (для API)
        """
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "phone_number": self.phone_number,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "photo_url": self.photo_url,
            "is_admin": bool(self.is_admin),
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
