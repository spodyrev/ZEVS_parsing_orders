"""
Главное приложение FastAPI
Веб-сервер для работы с заказами
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import uvicorn
from loguru import logger
from pathlib import Path
import os

from database import get_db, init_db
from models import Order, User
from config import settings
from scheduler import scheduler
from auth import (
    create_access_token,
    verify_telegram_auth,
    get_current_user,
    get_current_admin_user,
    get_current_superadmin_user,
    optional_auth
)


# Pydantic модели для API
class ManualOrderCreate(BaseModel):
    """Схема для создания заказа вручную"""
    tracking_number: Optional[str] = None
    supplier_name: Optional[str] = None
    description: Optional[str] = None
    total_price: Optional[float] = None
    currency: str = "CNY"
    order_date: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения
    """
    # Startup
    print("🚀 Запуск приложения...")
    init_db()
    
    # Запускаем планировщик автоматической синхронизации
    # Закомментируй эту строку, если не хочешь автоматическую синхронизацию
    scheduler.start()
    
    # Запускаем Telegram бота в отдельном потоке
    bot_task = None
    try:
        from telegram_bot.bot import start_bot
        import asyncio
        bot_task = asyncio.create_task(start_bot())
        logger.info("🤖 Telegram бот запущен")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось запустить Telegram бота: {e}")
    
    print(f"🌐 Сервер доступен по адресу: http://{settings.host}:{settings.port}")
    
    yield
    
    # Shutdown
    print("🛑 Остановка приложения...")
    if scheduler.is_running:
        scheduler.stop()
    
    if bot_task and not bot_task.done():
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass
        logger.info("🤖 Telegram бот остановлен")


# Создаем приложение FastAPI
app = FastAPI(
    title="ZEVS - Отслеживание заказов",
    description="Система отслеживания и управления заказами компании ZEVS",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware для безопасности
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler для 401 ошибок (перенаправление на страницу логина)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Обработка HTTP исключений
    
    При 401 ошибке (не авторизован) перенаправляем на страницу логина,
    если запрос был к HTML странице (не к API)
    """
    if exc.status_code == 401:
        # Проверяем, это запрос к API или к HTML странице
        if request.url.path.startswith("/api/"):
            # Для API возвращаем JSON
            return {"detail": exc.detail}
        else:
            # Для HTML страниц перенаправляем на логин
            return RedirectResponse(url="/login")
    
    # Для других ошибок используем стандартную обработку
    raise exc


# Определяем базовую директорию проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Подключаем статические файлы (CSS, JS)
static_dir = BASE_DIR / "frontend" / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Подключаем шаблоны HTML
templates_dir = BASE_DIR / "frontend" / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


def get_status_text(status: str) -> str:
    """
    Переводит статус заказа на русский
    """
    status_map = {
        'created': 'Создан',
        'paid': 'Оплачен',
        'shipped': 'В пути',
        'delivered': 'Доставлен',
        'cancelled': 'Отменен'
    }
    return status_map.get(status, status)


# ==================== Authentication endpoints ====================

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Страница логина с Telegram Login Widget
    """
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/api/auth/telegram/callback")
async def telegram_callback(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    id: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    photo_url: Optional[str] = None,
    auth_date: Optional[str] = None,
    hash: Optional[str] = None
):
    """
    Обработка callback от Telegram Login Widget
    
    Telegram перенаправляет сюда после успешной авторизации пользователя.
    Проверяем подпись, ищем пользователя в БД, создаем JWT токен.
    """
    try:
        # Собираем данные от Telegram
        auth_data = {
            'id': id,
            'first_name': first_name or '',
            'last_name': last_name or '',
            'username': username or '',
            'photo_url': photo_url or '',
            'auth_date': auth_date,
            'hash': hash
        }
        
        # Убираем None значения
        auth_data = {k: v for k, v in auth_data.items() if v is not None}
        
        # Проверяем подпись данных от Telegram
        if not verify_telegram_auth(auth_data):
            logger.warning(f"Invalid Telegram auth signature for user {id}")
            return RedirectResponse(url="/login?error=invalid_data")
        
        # Ищем пользователя по telegram_id
        user = db.query(User).filter(User.telegram_id == str(id)).first()
        
        if not user:
            # Пользователь не найден в БД - доступ запрещен
            logger.info(f"Unauthorized login attempt: telegram_id={id}, username={username}")
            return RedirectResponse(url="/login?error=unauthorized")
        
        # Проверяем, активен ли пользователь
        if not user.is_active:
            logger.info(f"Inactive user login attempt: {user.telegram_id}")
            return RedirectResponse(url="/login?error=inactive")
        
        # Обновляем информацию о пользователе из Telegram
        user.first_name = first_name or user.first_name
        user.last_name = last_name or user.last_name
        user.username = username or user.username
        user.photo_url = photo_url or user.photo_url
        user.last_login = datetime.now()
        
        db.commit()
        
        # Создаем JWT токен
        access_token = create_access_token(
            data={"sub": str(user.telegram_id)},
            expires_delta=timedelta(days=7)
        )
        
        # Перенаправляем на главную страницу и устанавливаем cookie
        redirect_response = RedirectResponse(url="/", status_code=302)
        redirect_response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,  # Защита от XSS
            max_age=7 * 24 * 60 * 60,  # 7 дней
            samesite="lax"  # Защита от CSRF
        )
        
        logger.info(f"✅ User logged in: {user.telegram_id} ({user.first_name} {user.last_name})")
        
        return redirect_response
        
    except Exception as e:
        logger.error(f"Error in telegram_callback: {e}")
        return RedirectResponse(url="/login?error=auth_failed")


@app.get("/api/auth/logout")
async def logout(response: Response):
    """
    Выход из системы
    
    Удаляет JWT токен из cookies
    """
    redirect_response = RedirectResponse(url="/login", status_code=302)
    redirect_response.delete_cookie("access_token")
    
    return redirect_response


@app.get("/api/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Получить информацию о текущем авторизованном пользователе
    
    Полезно для проверки авторизации со стороны frontend
    """
    return current_user.to_dict()


# ==================== Admin Panel endpoints ====================

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Страница админ-панели для управления пользователями
    Доступна только администраторам
    """
    users = db.query(User).order_by(User.created_at.desc()).all()
    
    # Статистика
    total_users = len(users)
    active_users = sum(1 for u in users if u.is_active)
    admin_users = sum(1 for u in users if u.is_admin)
    superadmin_users = sum(1 for u in users if u.is_superadmin)
    
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "users": users,
            "total_users": total_users,
            "active_users": active_users,
            "admin_users": admin_users,
            "superadmin_users": superadmin_users,
            "current_user": admin  # Передаем текущего пользователя для проверки прав
        }
    )


class UserCreate(BaseModel):
    """Схема для создания пользователя"""
    telegram_id: str
    phone_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_admin: int = 0
    is_superadmin: int = 0


class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    phone_number: Optional[str] = None
    is_admin: Optional[int] = None
    is_superadmin: Optional[int] = None


@app.get("/api/admin/users")
async def get_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Получить список всех пользователей
    Только для администраторов
    """
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [user.to_dict() for user in users]


@app.get("/api/admin/users/{user_id}")
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Получить информацию о конкретном пользователе
    Только для администраторов
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return user.to_dict()


@app.post("/api/admin/users")
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Создать нового пользователя
    Только для администраторов
    
    Суперадмины могут создавать любых пользователей (включая админов и суперадминов)
    Обычные админы могут создавать только обычных пользователей
    """
    try:
        # Проверяем права на создание администраторов
        if (user_data.is_admin or user_data.is_superadmin) and not admin.is_superadmin:
            raise HTTPException(
                status_code=403, 
                detail="Только суперадминистраторы могут назначать права администратора"
            )
        
        # Проверяем, не существует ли уже пользователь с таким telegram_id
        existing_user = db.query(User).filter(User.telegram_id == user_data.telegram_id).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Пользователь с таким Telegram ID уже существует")
        
        # Создаем нового пользователя
        new_user = User(
            telegram_id=user_data.telegram_id,
            phone_number=user_data.phone_number,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_admin=user_data.is_admin,
            is_superadmin=user_data.is_superadmin,
            is_active=1
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"✅ New user created by admin: telegram_id={new_user.telegram_id}")
        
        return {
            "status": "success",
            "message": "Пользователь создан",
            "user": new_user.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка создания пользователя: {str(e)}")


@app.put("/api/admin/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Обновить данные пользователя
    Только для администраторов
    
    Суперадмины могут изменять любые права
    Обычные админы могут изменять только номер телефона
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Проверяем права на изменение ролей
        if (user_data.is_admin is not None or user_data.is_superadmin is not None) and not admin.is_superadmin:
            raise HTTPException(
                status_code=403,
                detail="Только суперадминистраторы могут изменять права администратора"
            )
        
        # Обновляем поля
        if user_data.phone_number is not None:
            user.phone_number = user_data.phone_number
        
        if user_data.is_admin is not None:
            user.is_admin = user_data.is_admin
        
        if user_data.is_superadmin is not None:
            user.is_superadmin = user_data.is_superadmin
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"✏️ User updated by admin: user_id={user_id}")
        
        return {
            "status": "success",
            "message": "Данные пользователя обновлены",
            "user": user.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка обновления пользователя: {str(e)}")


@app.delete("/api/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Удалить пользователя
    Только для администраторов
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Нельзя удалить самого себя
        if user.id == admin.id:
            raise HTTPException(status_code=400, detail="Нельзя удалить самого себя")
        
        db.delete(user)
        db.commit()
        
        logger.info(f"🗑️ User deleted by admin: user_id={user_id}")
        
        return {
            "status": "success",
            "message": "Пользователь удален"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка удаления пользователя: {str(e)}")


@app.post("/api/admin/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Активировать/деактивировать пользователя
    Только для администраторов
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Нельзя деактивировать самого себя
        if user.id == admin.id:
            raise HTTPException(status_code=400, detail="Нельзя деактивировать самого себя")
        
        # Переключаем статус
        user.is_active = 1 if user.is_active == 0 else 0
        db.commit()
        
        status_text = "активирован" if user.is_active else "деактивирован"
        logger.info(f"🔄 User {status_text} by admin: user_id={user_id}")
        
        return {
            "status": "success",
            "message": f"Пользователь {status_text}",
            "is_active": bool(user.is_active)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling user status: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка изменения статуса: {str(e)}")


# ==================== Protected routes (existing) ====================

@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Главная страница с списком заказов (только активные, без архивных и удалённых)
    Требует авторизации
    """
    orders = db.query(Order).filter(
        Order.archived == 0,
        Order.deleted_at.is_(None)
    ).order_by(Order.created_at.desc()).all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "orders": orders,
            "total_orders": len(orders),
            "get_status_text": get_status_text  # Передаем функцию в шаблон
        }
    )


@app.get("/archive", response_class=HTMLResponse)
async def archive(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Страница с архивными заказами (без удалённых)
    Требует авторизации
    """
    orders = db.query(Order).filter(
        Order.archived == 1,
        Order.deleted_at.is_(None)
    ).order_by(Order.created_at.desc()).all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "orders": orders,
            "total_orders": len(orders),
            "get_status_text": get_status_text,
            "is_archive": True  # Флаг для шаблона
        }
    )


@app.get("/trash", response_class=HTMLResponse)
async def trash(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Страница корзины с удалёнными заказами
    Требует авторизации
    """
    orders = db.query(Order).filter(
        Order.deleted_at.isnot(None)
    ).order_by(Order.deleted_at.desc()).all()
    
    return templates.TemplateResponse(
        "trash.html",
        {
            "request": request,
            "orders": orders,
            "total_orders": len(orders),
            "get_status_text": get_status_text
        }
    )


# ==================== API эндпоинты ====================

@app.get("/api/orders", response_model=List[dict])
async def get_orders(db: Session = Depends(get_db)):
    """
    Получить список всех заказов
    
    Пример ответа:
    [
        {
            "id": 1,
            "order_id": "TB123456789",
            "status": "shipped",
            "tracking_number": "RF123456789CN",
            ...
        }
    ]
    """
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return [order.to_dict() for order in orders]


@app.get("/api/orders/{order_id}")
async def get_order(order_id: str, db: Session = Depends(get_db)):
    """
    Получить информацию о конкретном заказе
    """
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order.to_dict()


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """
    Получить статистику по заказам
    
    Возвращает количество заказов в каждом статусе
    """
    total = db.query(Order).count()
    
    stats = {
        "total": total,
        "by_status": {}
    }
    
    # Подсчитываем количество заказов для каждого статуса
    statuses = ["created", "paid", "shipped", "delivered", "cancelled"]
    for status in statuses:
        count = db.query(Order).filter(Order.status == status).count()
        stats["by_status"][status] = count
    
    return stats


@app.post("/api/sync")
async def sync_orders(db: Session = Depends(get_db)):
    """
    Запустить синхронизацию заказов вручную
    """
    try:
        scheduler.sync_orders()
        return {
            "status": "success",
            "message": "Синхронизация завершена",
            "last_sync": scheduler.last_sync.isoformat() if scheduler.last_sync else None
        }
    except Exception as e:
        logger.error(f"Ошибка синхронизации: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scheduler/status")
async def scheduler_status():
    """
    Получить статус планировщика
    """
    return scheduler.get_status()


@app.post("/api/scheduler/start")
async def start_scheduler():
    """
    Запустить планировщик автоматической синхронизации
    """
    if scheduler.is_running:
        return {"status": "info", "message": "Планировщик уже запущен"}
    
    scheduler.start()
    return {"status": "success", "message": "Планировщик запущен"}


@app.post("/api/scheduler/stop")
async def stop_scheduler():
    """
    Остановить планировщик автоматической синхронизации
    """
    if not scheduler.is_running:
        return {"status": "info", "message": "Планировщик не запущен"}
    
    scheduler.stop()
    return {"status": "success", "message": "Планировщик остановлен"}


@app.get("/api/auth/status")
async def auth_status():
    """
    Проверить статус авторизации на Taobao
    
    TODO: Проверка валидности сохраненных cookies
    """
    return {
        "authenticated": False,
        "message": "Авторизация еще не настроена"
    }


# ВАЖНО: Batch endpoints должны быть ПЕРЕД single order endpoints!
# Иначе FastAPI будет думать, что "batch" - это order_id

@app.post("/api/orders/batch/archive")
async def archive_orders_batch(request: Request, db: Session = Depends(get_db)):
    """
    Массовое архивирование заказов
    Принимает JSON: {"order_ids": ["id1", "id2", ...]}
    """
    data = await request.json()
    order_ids = data.get("order_ids", [])
    
    if not order_ids:
        raise HTTPException(status_code=400, detail="Не указаны ID заказов")
    
    # Архивируем все заказы
    archived_count = 0
    for order_id in order_ids:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if order:
            order.archived = 1
            archived_count += 1
    
    db.commit()
    
    return {
        "status": "success",
        "message": f"Архивировано заказов: {archived_count}",
        "archived_count": archived_count
    }


@app.post("/api/orders/batch/unarchive")
async def unarchive_orders_batch(request: Request, db: Session = Depends(get_db)):
    """
    Массовое восстановление заказов из архива
    Принимает JSON: {"order_ids": ["id1", "id2", ...]}
    """
    data = await request.json()
    order_ids = data.get("order_ids", [])
    
    if not order_ids:
        raise HTTPException(status_code=400, detail="Не указаны ID заказов")
    
    # Восстанавливаем все заказы
    unarchived_count = 0
    for order_id in order_ids:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if order:
            order.archived = 0
            unarchived_count += 1
    
    db.commit()
    
    return {
        "status": "success",
        "message": f"Восстановлено заказов: {unarchived_count}",
        "unarchived_count": unarchived_count
    }


@app.post("/api/orders/{order_id}/archive")
async def archive_order(order_id: str, db: Session = Depends(get_db)):
    """
    Архивирует заказ (убирает из активных)
    """
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    order.archived = 1
    db.commit()
    
    return {
        "status": "success",
        "message": f"Заказ {order_id} перемещен в архив"
    }


@app.post("/api/orders/{order_id}/unarchive")
async def unarchive_order(order_id: str, db: Session = Depends(get_db)):
    """
    Восстанавливает заказ из архива
    """
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    order.archived = 0
    db.commit()
    
    return {
        "status": "success",
        "message": f"Заказ {order_id} восстановлен из архива"
    }


@app.post("/api/orders/{order_id}/warehouse/toggle")
async def toggle_warehouse_status(order_id: str, db: Session = Depends(get_db)):
    """
    Переключает статус "Получен на складе"
    """
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # Переключаем статус
    order.received_at_warehouse = 1 if order.received_at_warehouse == 0 else 0
    db.commit()
    
    status_text = "получен на складе" if order.received_at_warehouse == 1 else "снят со склада"
    
    return {
        "status": "success",
        "message": f"Заказ {order_id} {status_text}",
        "received_at_warehouse": bool(order.received_at_warehouse)
    }


@app.get("/api/orders/active/list", response_model=List[dict])
async def get_active_orders(db: Session = Depends(get_db)):
    """
    Получить список только активных заказов (не архивированных)
    """
    orders = db.query(Order).filter(Order.archived == 0).order_by(Order.created_at.desc()).all()
    return [order.to_dict() for order in orders]


@app.get("/api/orders/archived/list", response_model=List[dict])
async def get_archived_orders(db: Session = Depends(get_db)):
    """
    Получить список архивированных заказов
    """
    orders = db.query(Order).filter(Order.archived == 1).order_by(Order.created_at.desc()).all()
    return [order.to_dict() for order in orders]


@app.get("/api/orders/{order_id}/warehouse-photos")
async def get_warehouse_photos_list(order_id: str, db: Session = Depends(get_db)):
    """
    Получить список фото товара со склада
    """
    order = db.query(Order).filter(Order.order_id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    if not order.warehouse_photo_path:
        return {"photos": []}
    
    # Парсим JSON массив фото
    import json as json_lib
    photos = []
    try:
        if order.warehouse_photo_path.startswith('['):
            photos = json_lib.loads(order.warehouse_photo_path)
        else:
            photos = [order.warehouse_photo_path]
    except:
        photos = [order.warehouse_photo_path]
    
    return {"photos": photos, "order_id": order_id}


@app.get("/api/orders/{order_id}/warehouse-photo/{photo_index}")
async def get_warehouse_photo(order_id: str, photo_index: int = 0, db: Session = Depends(get_db)):
    """
    Получить конкретное фото товара со склада по индексу
    """
    order = db.query(Order).filter(Order.order_id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    if not order.warehouse_photo_path:
        raise HTTPException(status_code=404, detail="Фото не найдено")
    
    # Парсим JSON массив фото
    import json as json_lib
    photos = []
    try:
        if order.warehouse_photo_path.startswith('['):
            photos = json_lib.loads(order.warehouse_photo_path)
        else:
            photos = [order.warehouse_photo_path]
    except:
        photos = [order.warehouse_photo_path]
    
    if photo_index >= len(photos):
        raise HTTPException(status_code=404, detail="Фото с таким индексом не найдено")
    
    photo_filename = photos[photo_index]
    
    # Полный путь к фото
    photo_path = Path(__file__).parent.parent / "warehouse_photos" / photo_filename
    
    if not photo_path.exists():
        raise HTTPException(status_code=404, detail="Файл фото не найден")
    
    return FileResponse(
        path=str(photo_path),
        media_type="image/jpeg",
        filename=photo_filename
    )


@app.get("/api/orders/{order_id}")
async def get_order(order_id: str, db: Session = Depends(get_db)):
    """
    Получает данные одного заказа по ID
    """
    order = db.query(Order).filter(Order.order_id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    return order.to_dict()


@app.put("/api/orders/{order_id}")
async def update_order(order_id: str, order_data: ManualOrderCreate, db: Session = Depends(get_db)):
    """
    Обновляет данные заказа
    """
    try:
        # Ищем заказ
        order = db.query(Order).filter(Order.order_id == order_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        # Обновляем поля (только те, что были переданы)
        if order_data.tracking_number is not None:
            order.tracking_number = order_data.tracking_number
        
        if order_data.supplier_name is not None:
            order.translated_description = order_data.supplier_name  # Имя поставщика
        
        if order_data.description is not None:
            order.description = order_data.description
        
        if order_data.total_price is not None:
            order.total_price = order_data.total_price
        
        if order_data.currency is not None:
            order.currency = order_data.currency
        
        if order_data.order_date is not None:
            try:
                order.order_date = datetime.fromisoformat(order_data.order_date.replace('Z', '+00:00'))
            except:
                pass
        
        # Обновляем время изменения
        order.updated_at = datetime.now()
        
        db.commit()
        db.refresh(order)
        
        logger.info(f"✏️ Заказ обновлён: {order_id}")
        
        return {
            "status": "success",
            "message": "Заказ успешно обновлён",
            "order": order.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении заказа: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении заказа: {str(e)}")


@app.delete("/api/orders/{order_id}")
async def delete_order(order_id: str, db: Session = Depends(get_db)):
    """
    Перемещает заказ в корзину (мягкое удаление)
    """
    try:
        # Ищем заказ
        order = db.query(Order).filter(Order.order_id == order_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        # Мягкое удаление - устанавливаем deleted_at
        order.deleted_at = datetime.now()
        db.commit()
        
        logger.info(f"🗑️ Заказ перемещён в корзину: {order_id}")
        
        return {
            "status": "success",
            "message": "Заказ перемещён в корзину"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении заказа: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении заказа: {str(e)}")


@app.post("/api/orders/manual")
async def create_manual_order(order_data: ManualOrderCreate, db: Session = Depends(get_db)):
    """
    Создает заказ вручную
    Все поля необязательные (кроме статуса и валюты, которые имеют значения по умолчанию)
    """
    try:
        # Парсим дату заказа, если она предоставлена
        order_date = None
        if order_data.order_date:
            try:
                order_date = datetime.fromisoformat(order_data.order_date.replace('Z', '+00:00'))
            except:
                order_date = datetime.now()
        else:
            order_date = datetime.now()
        
        # Генерируем order_id если не указан
        order_id = f"MANUAL_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Создаем новый заказ
        # Используем translated_description для хранения имени поставщика (временно)
        new_order = Order(
            order_id=order_id,
            tracking_number=order_data.tracking_number,
            status="created",  # По умолчанию "создан" для ручных заказов
            description=order_data.description,
            translated_description=order_data.supplier_name,  # Имя поставщика
            product_url=None,  # Убрали поле ссылки на товар
            total_price=order_data.total_price,
            currency=order_data.currency,
            items_count=1,  # По умолчанию 1
            order_date=order_date,
            archived=False
        )
        
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        
        logger.info(f"✅ Вручную добавлен заказ: {new_order.order_id or new_order.tracking_number or f'ID={new_order.id}'}")
        
        return {
            "status": "success",
            "message": "Заказ успешно добавлен",
            "order": new_order.to_dict()
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении заказа вручную: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при добавлении заказа: {str(e)}")


# Для разработки и тестирования
@app.get("/api/test/add-order")
async def test_add_order(db: Session = Depends(get_db)):
    """
    Тестовый эндпоинт для добавления фейкового заказа
    Только для разработки!
    """
    from datetime import datetime
    
    test_order = Order(
        order_id=f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}",
        tracking_number="RF123456789CN",
        status="shipped",
        description="小米手机 14 Pro 智能手机 5G",  # Xiaomi Phone 14 Pro на китайском
        product_url="https://item.taobao.com/item.htm?id=123456789",
        product_image_url="https://img.alicdn.com/imgextra/i4/O1CN01234567890.jpg_430x430q90.jpg",
        items_count=1,
        total_price=299.99,
        currency="CNY",
        order_date=datetime.now()
    )
    
    db.add(test_order)
    db.commit()
    db.refresh(test_order)
    
    return {
        "status": "success",
        "message": "Тестовый заказ добавлен",
        "order": test_order.to_dict()
    }


@app.get("/taobao-setup")
async def taobao_setup_page(request: Request, current_user: User = Depends(get_current_admin_user)):
    """Страница настройки Taobao (только для администраторов)"""
    return templates.TemplateResponse("taobao_setup.html", {"request": request})


@app.get("/api/taobao/status")
async def check_taobao_status(current_user: User = Depends(get_current_user)):
    """Проверка наличия Taobao cookies"""
    from pathlib import Path
    
    cookies_file = Path(__file__).parent.parent / "taobao_cookies.json"
    has_cookies = cookies_file.exists()
    
    return {
        "has_cookies": has_cookies,
        "cookies_file": str(cookies_file) if has_cookies else None
    }


@app.post("/api/taobao/upload-cookies")
async def upload_taobao_cookies(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_user)
):
    """Загрузка Taobao cookies файла (только для администраторов)"""
    from pathlib import Path
    import json
    
    try:
        # Читаем содержимое файла
        content = await file.read()
        
        # Парсим JSON
        cookies_data = json.loads(content.decode('utf-8'))
        
        # Проверяем что это валидный формат cookies
        if not isinstance(cookies_data, (list, dict)):
            raise HTTPException(status_code=400, detail="Invalid cookies format")
        
        # Сохраняем файл
        cookies_file = Path(__file__).parent.parent / "taobao_cookies.json"
        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(cookies_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Taobao cookies успешно загружены пользователем {current_user.telegram_id}")
        
        return {
            "status": "success",
            "message": "Cookies успешно загружены",
            "has_cookies": True
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке cookies: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading cookies: {str(e)}")


@app.post("/api/setup/create-first-admin")
async def create_first_admin(
    telegram_id: str,
    secret: str,
    first_name: str = "Admin",
    db: Session = Depends(get_db)
):
    """
    Временный endpoint для создания первого суперадминистратора
    Используйте только один раз при первом деплое!
    
    После создания первого суперадмина УДАЛИТЕ этот endpoint для безопасности!
    """
    # Проверка секретного кода
    if secret != settings.secret_key:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    # Проверяем что суперадминистраторов еще нет
    superadmin_count = db.query(User).filter(User.is_superadmin == 1).count()
    if superadmin_count > 0:
        raise HTTPException(status_code=400, detail="Superadmin already exists. Remove this endpoint!")
    
    # Создаем суперадминистратора
    admin = User(
        telegram_id=telegram_id,
        first_name=first_name,
        is_admin=1,
        is_superadmin=1,
        is_active=1,
        created_at=datetime.now()
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    logger.info(f"✅ First superadmin created: telegram_id={telegram_id}")
    
    return {
        "status": "success",
        "message": "First superadmin created successfully! Now remove this endpoint for security.",
        "admin": admin.to_dict()
    }


if __name__ == "__main__":
    # Запуск сервера
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug  # Автоперезагрузка при изменении кода
    )


@app.post("/api/trash/restore/{order_id}")
async def restore_order(order_id: str, db: Session = Depends(get_db)):
    """
    Восстанавливает заказ из корзины
    """
    try:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        if not order.deleted_at:
            raise HTTPException(status_code=400, detail="Заказ не находится в корзине")
        
        # Восстанавливаем заказ
        order.deleted_at = None
        db.commit()
        
        logger.info(f"♻️ Заказ восстановлен из корзины: {order_id}")
        
        return {
            "status": "success",
            "message": "Заказ восстановлен"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при восстановлении заказа: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при восстановлении заказа: {str(e)}")


@app.delete("/api/trash/permanent/{order_id}")
async def permanent_delete_order(order_id: str, db: Session = Depends(get_db)):
    """
    Окончательно удаляет заказ из базы данных (из корзины)
    """
    try:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        # Удаляем фотографии склада, если есть
        if order.warehouse_photo_path:
            import json as json_lib
            try:
                if order.warehouse_photo_path.startswith('['):
                    photos = json_lib.loads(order.warehouse_photo_path)
                else:
                    photos = [order.warehouse_photo_path]
                
                for photo_filename in photos:
                    photo_path = Path(__file__).parent.parent / "warehouse_photos" / photo_filename
                    if photo_path.exists():
                        photo_path.unlink()
                        logger.info(f"🗑️ Удалено фото: {photo_filename}")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при удалении фото: {e}")
        
        # Окончательно удаляем заказ
        db.delete(order)
        db.commit()
        
        logger.info(f"🗑️ Заказ окончательно удалён: {order_id}")
        
        return {
            "status": "success",
            "message": "Заказ окончательно удалён"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении заказа: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении заказа: {str(e)}")


@app.delete("/api/trash/clear")
async def clear_trash(db: Session = Depends(get_db)):
    """
    Очищает всю корзину (удаляет все заказы с deleted_at)
    """
    try:
        # Находим все удалённые заказы
        orders = db.query(Order).filter(Order.deleted_at.isnot(None)).all()
        
        deleted_count = 0
        for order in orders:
            # Удаляем фотографии
            if order.warehouse_photo_path:
                import json as json_lib
                try:
                    if order.warehouse_photo_path.startswith('['):
                        photos = json_lib.loads(order.warehouse_photo_path)
                    else:
                        photos = [order.warehouse_photo_path]
                    
                    for photo_filename in photos:
                        photo_path = Path(__file__).parent.parent / "warehouse_photos" / photo_filename
                        if photo_path.exists():
                            photo_path.unlink()
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при удалении фото: {e}")
            
            db.delete(order)
            deleted_count += 1
        
        db.commit()
        
        logger.info(f"🗑️ Корзина очищена. Удалено заказов: {deleted_count}")
        
        return {
            "status": "success",
            "message": f"Корзина очищена. Удалено заказов: {deleted_count}",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке корзины: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при очистке корзины: {str(e)}")


@app.delete("/api/trash/auto-clean")
async def auto_clean_trash(db: Session = Depends(get_db)):
    """
    Автоматически удаляет заказы старше 30 дней из корзины
    """
    try:
        from datetime import timedelta
        
        # Дата 30 дней назад
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # Находим старые удалённые заказы
        orders = db.query(Order).filter(
            Order.deleted_at.isnot(None),
            Order.deleted_at < thirty_days_ago
        ).all()
        
        deleted_count = 0
        for order in orders:
            # Удаляем фотографии
            if order.warehouse_photo_path:
                import json as json_lib
                try:
                    if order.warehouse_photo_path.startswith('['):
                        photos = json_lib.loads(order.warehouse_photo_path)
                    else:
                        photos = [order.warehouse_photo_path]
                    
                    for photo_filename in photos:
                        photo_path = Path(__file__).parent.parent / "warehouse_photos" / photo_filename
                        if photo_path.exists():
                            photo_path.unlink()
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при удалении фото: {e}")
            
            db.delete(order)
            deleted_count += 1
        
        db.commit()
        
        logger.info(f"🗑️ Автоочистка корзины. Удалено заказов старше 30 дней: {deleted_count}")
        
        return {
            "status": "success",
            "message": f"Автоочистка завершена. Удалено заказов: {deleted_count}",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка при автоочистке корзины: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при автоочистке корзины: {str(e)}")
