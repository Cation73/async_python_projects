import logging
import sys
import time

from fastapi import APIRouter, Depends, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import LOGGING
from db.db import get_session, redis_session
from schemas.model import PingModel


# Объект router, в котором регистрируем обработчики
api_router = APIRouter()

logging.config.dictConfig(LOGGING)
logger = logging.getLogger("api_logger")


# получение информации
# про версию приложения и python
@api_router.get("/info")
async def get_info_handler():
    return {
            "api": "v1",
            "python": sys.version_info
    }


# проверка доступности инфраструктуры
@api_router.get("/ping",
                response_model=PingModel,
                status_code=status.HTTP_200_OK,
                description="Проверка доступности инфраструктуры")
async def get_status_infra(*,
                           db: AsyncSession = Depends(get_session)) -> dict:
    logger.info("Execute postgres - check ping")
    try:
        pg_start_time = time.time()
        await db.execute(statement=select(1))
        pg_end_time = time.time() - pg_start_time
    except Exception as error:
        pg_end_time = None
        logger.error(f"Error ping postgres: {error}")

    logger.info("Execute redis - check ping")
    try:
        rd_start_time = time.time()
        r = redis_session()
        async with r.pipeline(transaction=True) as pipe:
            await pipe.get("nothing").execute()
        rd_end_time = time.time() - rd_start_time
    except Exception as error:
        rd_end_time = None
        logger.error(f"Error ping redis: {error}")

    return {"postgres": pg_end_time,
            "redis": rd_end_time}
