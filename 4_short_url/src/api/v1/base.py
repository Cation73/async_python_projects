import logging
import sys
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from core.logger import LOGGING
from db.db import get_session
from schemas import model as schema
from services.shorturl import url_crud


# Объект router, в котором регистрируем обработчики
api_router = APIRouter()

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('api_logger')


# получение информации
# про версию приложения и python
@api_router.get('/info')
async def info_handler():
    return {
        'api': 'v1',
        'python': sys.version_info
    }


@api_router.post("/url",
                 response_model=schema.ShortURL,
                 status_code=status.HTTP_201_CREATED,
                 description="Cоздание сокращенного урла")
async def create_url(*,
                     db: AsyncSession = Depends(get_session),
                     schema_short_url: schema.ShortURLCreate) -> Any:
    short_url = await url_crud.create(db=db,
                                      obj_in=schema_short_url)
    logger.info("ShortURL was created")
    return short_url


# проверка пингуется ли бд
@api_router.get('/ping')
async def get_db_status(*,
                        db: AsyncSession = Depends(get_session)) -> dict:
    try:
        conn = await db.connection()
        if conn:
            logger.info('The database is available')
            return {'Status DB': 'available'}
    except Exception as error:
        logger.error(f'The database is unavailable. Reason: {error}')
        return {'Status DB': 'unavailable'}


@api_router.get('/{short_url}',
                response_model=list[schema.ShortURL],
                description="Получение полного урла по короткому")
async def get_url(*,
                  db: AsyncSession = Depends(get_session),
                  short_url: str) -> Any:
    try:
        url = await url_crud.get(db=db,
                                 short_url=short_url)
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Internal Server Error: {error}")
    if not url:
        logger.warning("URL was't find")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="URL was't find")

    return RedirectResponse(url)


# получение статуса использования урла
@api_router.get('/{short_url}/status', response_model=schema.ShortURL)
async def get_status(*,
                     db: AsyncSession = Depends(get_session),
                     short_url: str) -> Any:
    try:
        status = await url_crud.get_status(db=db,
                                           short_url=short_url)
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Internal Server Error: {error}")

    if not status:
        logger.warning("Status was't find")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Status was't find")
    return status


@api_router.post('/batch_url',
                 response_model=schema.ShortURLCreateBatch,
                 status_code=status.HTTP_201_CREATED,
                 description="Отправка урлов батчами")
async def batch_upload(*,
                       db: AsyncSession = Depends(get_session),
                       batch_short_url: schema.ShortURLCreateBatch) -> str:
    try:
        short_url = await url_crud.create_multi(db=db,
                                                obj_in=batch_short_url)
        logger.info("Batch upload success")

        return short_url
    except Exception as error:
        logger.error(f"Error in batch_upload: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"{error}")

    
