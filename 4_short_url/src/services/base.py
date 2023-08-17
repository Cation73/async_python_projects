import secrets
import string
from abc import abstractmethod, ABC
from typing import Generic, Type, TypeVar
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from sqlalchemy import select, update

from db.db import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)


class Repository(ABC):

    @abstractmethod
    def resolve_short_url(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_status(self, *args, **kwargs):
        pass

    @abstractmethod
    def create(self, *args, **kwargs):
        pass

    @abstractmethod
    def create_multi(self, *args, **kwargs):
        pass


class RepositoryDB(Repository, Generic[ModelType, CreateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self._model = model

    async def get_clicks(self,
                         db: AsyncSession,
                         short_url: str) -> int:
        '''получение кликов'''

        statement = select(self._model) \
            .where(self._model.short_url == short_url)
        obj = await db.scalar(statement=statement)
        clicks = obj.clicks
        return clicks

    async def update_clicks(self,
                            db: AsyncSession,
                            short_url: str,
                            clicks: int) -> None:
        '''обновление количества кликов'''

        statement = update(self._model) \
            .filter_by(short_url=short_url).values(clicks=clicks + 1)
        await db.execute(statement=statement)
        await db.commit()

    async def resolve_short_url(self,
                                db: AsyncSession,
                                short_url: str) -> ModelType:
        '''получение результата'''

        statement = select(self._model.url) \
            .where(self._model.short_url == short_url)
        clicks = await self.get_clicks(db, short_url)
        await self.update_clicks(db=db, short_url=short_url, clicks=clicks)
        result = await db.scalar(statement=statement)
        return result

    async def get_status(self,
                         db: AsyncSession,
                         short_url: str) -> ModelType:
        '''получение статуса'''

        statement = select(self._model) \
            .where(self._model.short_url == short_url)
        result = await db.execute(statement=statement)
        return result.scalar()

    @staticmethod
    def short_url(length: int = 8) -> str:
        '''функция генерации короткого url'''

        chars = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(chars) for _ in range(length))

    async def create(self,
                     db: AsyncSession, *,
                     obj_in: CreateSchemaType) -> ModelType:
        '''создание и запись короткого url'''

        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self._model(**obj_in_data)
        db_obj.short_url = self.short_url()
        db.add(db_obj)
        # backoff не работал,
        # но кажется с помощью sqlalchemy это тоже можно реализовать
        try:
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except IntegrityError:
            db.rollback()

    async def create_multi(self,
                           db: AsyncSession, *,
                           obj_in: CreateSchemaType) -> ModelType:
        '''батчевое создание и запись коротких url'''

        obj_in_data = jsonable_encoder(obj_in)
        all_obj = []
        for obj in obj_in_data:
            db_obj = self._model(**obj)
            db_obj.short_url = self.short_url()
            all_obj.append(db_obj)
        db.add_all(all_obj)
        try:
            await db.commit()
            for obj in all_obj:
                await db.refresh(obj)
            return all_obj
        except IntegrityError:
            db.rollback()
