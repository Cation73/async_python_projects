import os
import datetime

from dotenv import load_dotenv
from pydantic import BaseSettings, PostgresDsn, RedisDsn, Field

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AppSettings(BaseSettings):
    app_title: str = "storage"
    database_dsn: PostgresDsn = Field(..., env='POSTGRES_DSN')
    test_database_dsn: PostgresDsn = Field(..., env='TEST_POSTGRES_DSN')
    project_name: str = Field(..., env='PROJECT_NAME')
    project_host: str = Field(..., env='PROJECT_HOST')
    project_port: int = Field(..., env='PROJECT_PORT')
    redis_dsn: RedisDsn = Field(..., env='REDIS_DSN')

    upload_folder: str = Field(..., env='UPLOAD_FOLDER')
    expire_token: datetime.timedelta = datetime.timedelta(minutes=10)
    expire_redis: datetime.timedelta = datetime.timedelta(minutes=25)
    
    secret_key: str = Field(..., env='secret_key')

    max_file_size_kb = Field(..., env='MAX_FILE_SIZE_KB')
    
    class Config:
        env_file = '.env'


app_settings = AppSettings()
