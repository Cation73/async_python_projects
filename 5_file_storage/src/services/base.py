import os
import io
import pathlib
import zipfile
import datetime
import logging
from typing import Union, Any, Dict, Type, TypeVar

import aiofiles
from aiofiles import os as aio_os
from pydantic import BaseModel
from fastapi import File, HTTPException, status, UploadFile as upload_file, \
    Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.encoders import jsonable_encoder
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import Base
from core.logger import LOGGING
from core.config import app_settings
from schemas.model import FileUpload, FileUploadResponse, User, TokenData, \
    UserBase
from models.model import UserModel


# определение логгера
logging.config.dictConfig(LOGGING)
logger = logging.getLogger('api_logger')

# определение типов
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")


class BaseService():
    def __init__(self,
                 model: Union[Type[ModelType], None] = None):
        self._model = model

    def set_params(self,
                   statement: select,
                   params: dict,
                   skip: int = 0,
                   limit: int = 100) -> select:
        filters = [getattr(self._model, key) == value for key, value in params.items()]
        if filters:
            statement = statement.where(and_(*filters))
        statement = statement.offset(skip).limit(limit)

        return statement

    async def get(self,
                  db: AsyncSession,
                  is_one: bool = False,
                  **kwargs: Dict[str, Any]) -> Union[Type[ModelType], None]:

        statement = select(self._model).where(self._model.id == id)
        statement = self.set_params(statement, self._model, kwargs)

        result = await db.execute(statement=statement)
        if is_one:
            return result.unique().scalar_one_or_none()
        else:
            return result.unique().scalars().all()

    async def create(self,
                     *,
                     db: AsyncSession = None,
                     object_in: Type[CreateSchemaType]) -> Type[ModelType]:
        object_in_data = jsonable_encoder(object_in)
        db_object = self.model(**object_in_data)
        db.add(db_object)
        try:
            await db.commit()
            await db.refresh(db_object)
            return db_object
        except Exception:
            raise

    async def update(self,
                     *,
                     db: AsyncSession,
                     db_object: Type[ModelType],
                     object_in: Union[Type[CreateSchemaType],
                                      Dict[str, Any]]) -> Type[ModelType]:

        statement = update(self.model).where(self.model.id == db_object.id). \
            values(object_in.dict(exclude_unset=True)).returning(self.model)

        await db.execute(statement=statement)
        await db.commit()
        return db_object


class UserCrud(BaseService):
    model = UserModel
    schema = User


class FileService(BaseService):
    async def upload(self,
                     user: UserBase,
                     file: upload_file,
                     path: Union[str, None]) -> FileUploadResponse:
        path = f"{path}/" if path else ""

        upload_file = await self.create(obj_in=FileUpload(name=file.filename,
                                                          path=os.path.join(path,
                                                                            file.filename),
                                                          user_id=user.id))

        directory = os.path.join(app_settings.upload_folder,
                                 user.username,
                                 path)

        path_directory = pathlib.Path(directory)

        max_file_size = app_settings.max_file_size_kb * 1024
        real_file_size = 0

        if not pathlib.Path.exists(path_directory):
            pathlib.Path(path_directory).mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(pathlib.Path(path_directory,
                                              file.filename),
                                 "wb") as f:

            while content := await file.read(1024):
                real_file_size += len(content)
                if real_file_size > max_file_size:
                    await aio_os.remove(path)
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                        detail="Errors by save file - so large file")
                await f.write(content)

        return FileUploadResponse(**upload_file.__dict__)

    async def download(self,
                       user: UserBase,
                       identifier: Union[str, None] = None,
                       path: Union[str, None] = None):

        if path:
            directory = os.path.join(app_settings.upload_folder,
                                     user.username,
                                     path)
            directory_files = [os.path.join(directory, file.name) for file
                               in list(pathlib.Path(directory).iterdir())]
            return self.zip_folder(directory_files)

        if identifier:
            file = await self.get(is_one=True, id=identifier)
            file_path = os.path.join(app_settings.upload_folder,
                                     user.username,
                                     file.path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return FileResponse(path=file_path,
                                    filename=file.name,
                                    media_type="application/octet-stream")

    def zip_folder(self,
                   file_list: list) -> File:
        bytes_io = io.BytesIO()
        zip_name = f"{str(datetime.now())}.zip"
        with zipfile.ZipFile(bytes_io, "w") as zip:
            for file in file_list:
                zip.write(file)
        return StreamingResponse(iter([bytes_io.getvalue()]),
                                 media_type="application/x-zip-compressed",
                                 headers={"Content-Disposition":
                                          f"attachment filename={zip_name}"})


# Проверяет, что хеш от plain_password равен hashed_password
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


# Получение пользователя
async def get_user(username: str, user_crud: UserCrud) -> Union[User, None]:
    return await user_crud.get_one(username=username)  # type: ignore


#  Получаем хеш пароля
def get_password_hash(password: str):
    return pwd_context.hash(password)


# Авторизация пользователя
async def authenticate_user(form_data: OAuth2PasswordRequestForm = Depends(),
                            user_crud: UserCrud = Depends()) -> Union[User,
                                                                      bool]:
    user = await get_user(username=form_data.username, user_crud=user_crud)
    if not user:
        return False
    if not verify_password(form_data.password, user.password):
        return False
    return user


# Создание токена
def create_access_token(data: dict,
                        expires_delta: Union[datetime.timedelta,
                                             None] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + \
            datetime.timedelta(minutes=app_settings.expire_token)
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(to_encode,
                                  app_settings.secret_key,
                                  algorithm="HS256")
    return encoded_jwt


# Проверка валиден ли токен
async def get_current_user(token,
                           user_crud: UserCrud = Depends()):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, app_settings.secret_key,
                             algorithms="HS256")
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username, user_crud=user_crud)
    if user is None:
        raise credentials_exception
    return user
