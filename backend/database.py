"""
Настройка базы данных SQLite
Создание подключения и сессий
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Создаем движок базы данных
# echo=True показывает все SQL запросы в консоли (полезно для обучения)
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # Нужно для SQLite
    echo=settings.debug
)

# Создаем фабрику сессий
# Сессия - это как "разговор" с базой данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для всех моделей
Base = declarative_base()


def get_db():
    """
    Получить сессию базы данных
    Используется как dependency в FastAPI
    
    Пример использования:
    @app.get("/orders")
    def get_orders(db: Session = Depends(get_db)):
        return db.query(Order).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Инициализация базы данных
    Создает все таблицы, если их еще нет
    """
    from models import Order, User  # Импортируем модели
    Base.metadata.create_all(bind=engine)
    print("✅ База данных инициализирована")
