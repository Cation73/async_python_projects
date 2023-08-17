import logging
from typing import Union

from fastapi import APIRouter, Depends, status, File, UploadFile as upload_file
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import LOGGING
from db.db import get_session
from schemas.model import FileBase, UserBase, UserFiles
from models.model import FileModel
from services.base import FileService, get_current_user


# Объект router, в котором регистрируем обработчики
api_router = APIRouter()

logging.config.dictConfig(LOGGING)
logger = logging.getLogger("api_logger")


# информация о загруженных файлах
@api_router.get("/files",
                response_model=UserFiles,
                status_code=status.HTTP_200_OK,
                description="Информация о загруженных файлах")
async def user_files(*,
                     db: AsyncSession = Depends(get_session),
                     user: UserBase = Depends(get_current_user)):

    logger.info("Get files")
    files = await FileService(db, FileModel).get(user_id=user.id)
    return UserFiles(user_id=user.id,
                     files=[FileBase(**file.__dict__) for file in files])


# загрузка файлов в хранилище
@api_router.post("/files/upload",
                 response_model=None,
                 status_code=status.HTTP_201_CREATED,
                 description="Загрузка файлов в хранилище")
async def post_upload_files(*,
                            path: Union[str, None] = None,
                            db: AsyncSession = Depends(get_session),
                            user: UserBase = Depends(get_current_user),
                            file: upload_file = File()):
    logger.info("Post /files/upload")
    return await FileService(db, FileModel).upload(path, file, user)


# скачивание файлов из хранилища
@api_router.get("/files/download",
                description="Скачивание файлов из хранилища")
async def get_download_files(*,
                             identifier: Union[str, None] = None,
                             path: Union[str, None] = None,
                             db: AsyncSession = Depends(get_session),
                             user: UserBase = Depends(get_current_user)) -> FileResponse:
    logger.info("Get /files/download")
    return await FileService(db, FileModel).download(user, identifier, path)
