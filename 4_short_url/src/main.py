import uvicorn
import ipaddress
from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse

from core import config
from core.config import app_settings
from core.logger import LOGGING
from api.v1 import base

app = FastAPI(
    # Конфигурируем название проекта. Оно будет отображаться в документации
    title=app_settings.app_title,
    # Адрес документации в красивом интерфейсе
    docs_url='/api/openapi',
    # Адрес документации в формате OpenAPI
    openapi_url='/api/openapi.json',
    default_response_class=ORJSONResponse,
)

app.include_router(base.api_router, prefix="/api/v1")


@app.middleware("http")
async def check_forbidden_status(request: Request,
                                 call):
    host = request.client.host
    # не было опыта работы с ipadress, но постарался учесть замечание
    for subnet in app_settings.block_list:
        if ipaddress.IPv4Address(host) in subnet:
            return ORJSONResponse(status_code=status.HTTP_403_FORBIDDEN,
                                  content={"message": "Error 403 - Forbidden"})
    response = await call(request)
    return response

if __name__ == '__main__':
    # Приложение может запускаться командой
    # `uvicorn main:app --host 0.0.0.0 --port 8080`
    # но чтобы не терять возможность использовать дебагер,
    # запустим uvicorn сервер через python
    uvicorn.run(
        app,
        host=app_settings.host,
        port=app_settings.port
    )
