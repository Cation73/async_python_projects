import asyncio
import shutil
from pathlib import Path
from typing import AsyncGenerator, Callable, Generator

import pytest
import pytest_asyncio
from fastapi_cache import caches
from fastapi_cache.backends.redis import RedisCacheBackend
from httpx import AsyncClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from db.db import Base, get_session, redis_cache
from core.config import app_settings
from main import app

test_dsn = app_settings.test_database_dsn


def get_test_engine():
    return create_async_engine(test_dsn, echo=True, future=True)


def redis_test_cache():
    return caches.get('test_redis')


@pytest.fixture(scope='session')
def event_loop(request) -> Generator:
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope='session')
async def client() -> AsyncGenerator:
    async with AsyncClient(app=app, base_url=test_dsn) as client:
        yield client


@pytest_asyncio.fixture(scope='session')
async def async_session() -> AsyncGenerator:

    create_session: Callable = sessionmaker(engine, class_=AsyncSession, 
                                            expire_on_commit=False)
    async with create_session() as session_:
        yield session_


@pytest.fixture(scope="session")
def engine():
    engine = get_test_engine()
    yield engine
    engine.sync_engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def create_base(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="session")
async def test_app():
    app.dependency_overrides[get_session] = async_session

    rc = RedisCacheBackend(app_settings.REDIS_DSN)
    caches.set('test_redis', rc)

    app.dependency_overrides[redis_cache] = redis_test_cache
    yield app


@pytest_asyncio.fixture(scope="session")
async def auth_async_client(test_app):
    test_user = 'test1'
    test_password = test_user
    async with AsyncClient(app=test_app, base_url='http://127.0.0.1:8000/api/v1') as ac:
        await ac.post('/register/',
                      json={'username': test_user,
                            'password': test_password})
        response_success = await ac.post('/auth',
                                         json={'username': test_user,
                                               'password': test_password})
        token = 'Bearer ' + response_success.json()['access_token']
        ac.headers = {'Authorization': token}
        yield ac


@pytest_asyncio.fixture(scope="session")
async def auth_async_client_with_file(auth_async_client):
    path_of_upload_file = Path('test_file.txt')
    file = {'file': path_of_upload_file.open('rb')}
    await auth_async_client.post('/files/upload',
                                 params={'path': '/test'},
                                 files=file)
    yield auth_async_client
    shutil.rmtree(app_settings.upload_folder + '/test')
