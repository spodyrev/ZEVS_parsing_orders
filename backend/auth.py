"""
Модуль аутентификации
Работа с JWT токенами, Telegram Login Widget validation, dependencies для проверки авторизации
"""

import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from loguru import logger

from database import get_db
from models import User
from config import settings


# JWT настройки
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# Security scheme для Bearer токенов
security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Создает JWT токен для пользователя
    
    Args:
        data: Данные для токена (обычно {"sub": telegram_id})
        expires_delta: Время жизни токена (по умолчанию 7 дней)
    
    Returns:
        Закодированный JWT токен
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_telegram_auth(auth_data: dict) -> bool:
    """
    Проверяет подпись данных от Telegram Login Widget
    
    Telegram отправляет hash, который нужно проверить для безопасности.
    Документация: https://core.telegram.org/widgets/login#checking-authorization
    
    Args:
        auth_data: Словарь с данными от Telegram (id, first_name, last_name, username, photo_url, auth_date, hash)
    
    Returns:
        True если подпись валидна, False если нет
    """
    check_hash = auth_data.get('hash')
    if not check_hash:
        return False
    
    # Создаем копию данных без hash
    auth_data_copy = {k: v for k, v in auth_data.items() if k != 'hash'}
    
    # Сортируем ключи и создаем строку для проверки
    data_check_string = '\n'.join([f'{k}={v}' for k, v in sorted(auth_data_copy.items())])
    
    # Получаем secret_key из bot token
    # Используем SHA256 от bot token как ключ
    bot_token = settings.telegram_bot_token
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    
    # Вычисляем hash
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Проверяем, что hash совпадает
    is_valid = calculated_hash == check_hash
    
    # Дополнительно проверяем, что данные не старше 1 дня
    if is_valid:
        auth_date = int(auth_data.get('auth_date', 0))
        current_timestamp = int(datetime.now().timestamp())
        
        # 86400 секунд = 24 часа
        if current_timestamp - auth_date > 86400:
            logger.warning(f"Telegram auth data is too old: {current_timestamp - auth_date} seconds")
            return False
    
    return is_valid


def get_token_from_cookie(request: Request) -> Optional[str]:
    """
    Извлекает JWT токен из cookie
    
    Args:
        request: FastAPI Request объект
    
    Returns:
        Токен или None
    """
    return request.cookies.get("access_token")


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency для получения текущего авторизованного пользователя
    
    Проверяет JWT токен из cookie и возвращает пользователя.
    Если токен невалиден или пользователь не найден - выбрасывает HTTPException.
    
    Usage:
        @app.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id}
    
    Args:
        request: FastAPI Request
        db: Database session
    
    Returns:
        User объект
    
    Raises:
        HTTPException: 401 если пользователь не авторизован
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не авторизован",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Получаем токен из cookie
    token = get_token_from_cookie(request)
    
    if not token:
        logger.debug("No token in cookies")
        raise credentials_exception
    
    try:
        # Декодируем токен
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        telegram_id: str = payload.get("sub")
        
        if telegram_id is None:
            logger.warning("No telegram_id in token payload")
            raise credentials_exception
            
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise credentials_exception
    
    # Получаем пользователя из БД
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if user is None:
        logger.warning(f"User not found: telegram_id={telegram_id}")
        raise credentials_exception
    
    # Проверяем, что пользователь активен
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь деактивирован"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency для получения текущего активного пользователя
    
    Дополнительная проверка на is_active=1
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_active_user)):
            return {"user_id": user.id}
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь деактивирован"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency для получения текущего пользователя-администратора
    
    Проверяет что пользователь авторизован И является админом
    
    Usage:
        @app.get("/admin")
        async def admin_route(admin: User = Depends(get_current_admin_user)):
            return {"admin_id": admin.id}
    
    Args:
        current_user: Текущий пользователь
    
    Returns:
        User объект с is_admin=1
    
    Raises:
        HTTPException: 403 если пользователь не админ
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав. Требуются права администратора."
        )
    return current_user


def optional_auth(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Опциональная аутентификация - не выбрасывает исключение если пользователь не авторизован
    
    Полезно для страниц, которые доступны и анонимным пользователям, 
    но показывают дополнительную информацию авторизованным.
    
    Usage:
        @app.get("/")
        async def home(user: Optional[User] = Depends(optional_auth)):
            if user:
                return {"message": f"Welcome back, {user.first_name}!"}
            return {"message": "Welcome, guest!"}
    
    Args:
        request: FastAPI Request
        db: Database session
    
    Returns:
        User объект или None
    """
    try:
        token = get_token_from_cookie(request)
        if not token:
            return None
        
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        telegram_id: str = payload.get("sub")
        
        if telegram_id is None:
            return None
        
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        
        if user and user.is_active:
            return user
        
        return None
        
    except JWTError:
        return None
