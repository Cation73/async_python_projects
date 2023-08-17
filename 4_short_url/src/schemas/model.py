from typing import Optional
from datetime import datetime

from pydantic import BaseModel


# общие свойства
class ShortURLBase(BaseModel):
    url: str


# свойства, полученные при создании сущности
class ShortURLCreate(ShortURLBase):
    pass


# общие свойства, хранящиеся в БД
class ShortURLInDBBase(ShortURLBase):
    id: int
    url: str
    short_url: str
    created_at: datetime
    clicks: Optional[int]

    class Config:
        orm_mode = True


# свойства, возвращаемые пользователю
class ShortURL(ShortURLInDBBase):
    pass


# свойства, сохраняемые в БД
class ShortURLInDB(ShortURLInDBBase):
    pass


# свойства, полученные для батчевого создания
class ShortURLCreateBatch(BaseModel):
    batch: list[ShortURLBase]
