# использовал этот гайд https://fastapi.tiangolo.com/tutorial/testing/

from fastapi.testclient import TestClient
from http import HTTPStatus

from main import app

# класс для тестирования
client = TestClient(app)

# тестовые данные
body = {"url": "url"}

batch_upload = [{"url": "url"},
                {"url": "url2"}]


# тест команды проверки пинга БД
def test_ping():
    response = client.get('api/v1/ping')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'Status DB': 'available'}


# тест создания короткого url
def test_short_url():
    response = client.post('/api/v1/url', json=body)
    result = response.json()
    assert result.get('url') == 'url'


# тест создания коротких url батчами
def test_batch_upload():
    response = client.post('api/v1/batch_url', json=batch_upload)
    result = response.json()
    assert len(result) == 2
    assert result[1].get('url') == 'url2'


# тест статуса url
def test_status_url():
    response = client.get('api/v1/ABCD1/status')
    assert response.status_code == HTTPStatus.NOT_FOUND


# тест получения полного url по короткому
def test_get_url():
    response = client.get('api/v1/ABCD1/status')
    assert response.status_code == HTTPStatus.NOT_FOUND
