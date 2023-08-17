import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from core.config import app_settings
from core.logger import LOGGING
from api.v1 import files, ping, user


app = FastAPI(
    # Конфигурируем название проекта. Оно будет отображаться в документации
    title=app_settings.app_title,
    # Адрес документации в красивом интерфейсе
    docs_url='/api/openapi',
    # Адрес документации в формате OpenAPI
    openapi_url='/api/openapi.json',
    default_response_class=ORJSONResponse,
)

app.include_router(files.api_router, prefix="/api/v1", tags=["Files"])
app.include_router(user.api_router, prefix="/api/v1", tags=["Users"])
app.include_router(ping.api_router, prefix="/api/v1", tags=["Ping"])


if __name__ == '__main__':
    # Приложение может запускаться командой
    # `uvicorn main:app --host 0.0.0.0 --port 8080`
    # но чтобы не терять возможность использовать дебагер,
    # запустим uvicorn сервер через python
    uvicorn.run(
        app,
        host=app_settings.project_host,
        port=app_settings.project_port
    )
