# использовал этот гайд https://fastapi.tiangolo.com/tutorial/testing/
import pytest
from datetime import datetime
from httpx import AsyncClient
from fastapi.testclient import TestClient
from http import HTTPStatus
from pathlib import Path

from main import app


# класс для тестирования
client = TestClient(app)


# тест команды проверки пинга
@pytest.mark.asyncio
async def test_ping(test_app):
    async with AsyncClient(app=test_app, base_url='http://127.0.0.1:8000/api/v1') as ac:
        response = await ac.get(app.url_path_for(name='get_status_infra'))

        assert response.status_code == HTTPStatus.OK
        

# тест регистрации пользователя
@pytest.mark.asyncio
async def test_register(test_app):
    async with AsyncClient(app=test_app, base_url='http://127.0.0.1:8000/api/v1') as ac:
        test = datetime.utcnow()
        response_create = await ac.post(app.url_path_for(name='post_register_user'),
                                        json={'username': f'test{test}',
                                              'password': f'test{test}'})
        
        assert response_create.status_code == HTTPStatus.CREATED


# тест загрузки данных
@pytest.mark.asyncio
async def test_upload_file(auth_async_client):
    path_of_upload_file = Path('test_file.txt')
    file = {'file': path_of_upload_file.open('rb')}
    response = await auth_async_client.post(app.url_path_for(name='post_upload_files'),
                                            params={'path': '/test'},
                                            files=file)
    
    assert response.status_code == HTTPStatus.CREATED