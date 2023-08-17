import os
import ipaddress
from logging import config as logging_config
from pydantic import Field, BaseSettings, PostgresDsn

from core.logger import LOGGING

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)


# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AppSettings(BaseSettings):
    app_title: str = 'ShortURLApp'
    database_dsn: PostgresDsn = 'postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/project4'
    project_name: str = Field('ShortURL', env='PROJECT_NAME')
    host: str = Field('127.0.0.1', env='PROJECT_HOST')
    port: int = Field('8000', env='PROJECT_PORT')
    block_list: list = [ipaddress.IPv4Network('192.168.0.0/16'),
                        ipaddress.IPv4Network('10.0.0.0/8')]

    class Config:
        env_file = '.env'


app_settings = AppSettings()
