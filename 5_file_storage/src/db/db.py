import redis.asyncio as redis
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from fastapi_cache import caches
from fastapi_cache.backends.redis import CACHE_KEY

from core.config import app_settings


# Создаём базовый класс для будущих моделей
Base = declarative_base()
# Создаём движок
# Настройки подключения к БД передаём из переменных окружения,
# которые заранее загружены в файл настроек
engine = create_async_engine(app_settings.database_dsn, echo=True, future=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# Функция понадобится при внедрении зависимостей
# Dependency
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


# подключение для redis
async def redis_session():
    return await redis.from_url(app_settings.redis_dsn)


def redis_cache():
    return caches.get(CACHE_KEY)