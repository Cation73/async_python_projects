from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
# Импортируем базовый класс для моделей.
from db.db import Base


class ShortURL(Base):
    __tablename__ = 'shorturl'
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=False, nullable=False)
    short_url = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)
    clicks = Column(Integer, default=0)
