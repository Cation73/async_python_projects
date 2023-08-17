from datetime import datetime
from pydantic import UUID4, BaseModel, validator
from typing import Union, List
import re
import uuid


# для файлов
class FileBase(BaseModel):
    id: UUID4
    user_id: int
    name: str
    created_at: datetime
    path: str
    size: int
    is_downloadable: bool


class FileUpload(BaseModel):
    name: str
    path: str
    size: int
    user_id: int


class FileUploadResponse(FileBase):
    pass


# для пользователей
class IdSchema(BaseModel):
    id: uuid.UUID


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class CreateUser(BaseModel):
    username: str
    password: str

    @validator('username', always=True)
    def validate_username(cls, value):
        clear_username = re.sub(r'\W+', '', value)
        if value != clear_username:
            raise ValueError('Username must not contain any special characters')

        return value


class User(CreateUser, IdSchema):
    ...


# для пользователей
class ORMBase(BaseModel):

    username: str
    
    class Config:
        orm_model = True


class UserBase(ORMBase):
    id: int


class UserFiles(BaseModel):
    user_id: int
    files: List[FileBase]


# для проверки отклика
class PingModel(BaseModel):
    db: Union[float, None]
    cache: Union[float, None]
