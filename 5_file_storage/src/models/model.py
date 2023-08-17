from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy_utils import UUIDType

# Импортируем базовый класс для моделей.
from db.db import Base


class FileModel(Base):
    __tablename__ = "files"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False,
                     index=True)
    name = Column(String(125), nullable=False)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)
    path = Column(String(255), nullable=False, unique=True)
    is_downloadable = Column(Boolean, default=False)


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String(125), nullable=False, unique=True)
    password = Column(String(125), nullable=False)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)
