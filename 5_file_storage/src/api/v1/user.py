import logging
import datetime

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import IntegrityError

from core.logger import LOGGING
from core.config import app_settings
from schemas.model import User, Token, CreateUser
from services.base import UserCrud
from services.base import authenticate_user, \
    create_access_token, get_password_hash


# Объект router, в котором регистрируем обработчики
api_router = APIRouter()

logging.config.dictConfig(LOGGING)
logger = logging.getLogger("api_logger")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth")


# регистрация пользователя
@api_router.post("/register",
                 status_code=status.HTTP_201_CREATED,
                 description="Регистрация пользователя")
async def register(creds: CreateUser, user: UserCrud = Depends()):
    # получаем хеш пароля
    creds.password = get_password_hash(creds.password)
    try:
        return await user.create(creds)
    except (IntegrityError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Don't register")
    

# авторизация пользователя
@api_router.post("/auth",
                 response_model=Token,
                 description="Авторизация пользователя")
async def login_for_access_token(user: User = Depends(authenticate_user)):
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Don't auth")
    access_token_expires = datetime.timedelta(minutes=app_settings.expire_token)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
