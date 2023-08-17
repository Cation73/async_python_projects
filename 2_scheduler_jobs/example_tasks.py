import os

from logger import logger
from yw_api import YandexWeatherAPI


# создание директории
def create_folder(path_folder: str) -> None:
    try:
        logger.info(f'create folder {path_folder}')
        os.makedirs(path_folder)
    except Exception as error:
        logger.error(error)


# удаление директории
def delete_folder(path_folder: str) -> None:
    try:
        logger.info(f'delete folder {path_folder}')
        os.system(f'rm -rf {path_folder}')
    except Exception as error:
        logger.error(error)


# переименование директорий и файлов
def rename(old_name: str, new_name: str) -> None:
    try:
        logger.info(f'rename folder {old_name} to {new_name}')
        os.rename(f'{old_name}', f'{new_name}')
    except Exception as error:
        logger.error(error)
        raise Exception(error)


# создание файла
def create_file(file_name: str):
    if os.path.exists(file_name):
        raise Exception(f'{file_name} exists')
    logger.info(f'create the {file_name}')
    with open(file_name, 'w'):
        pass


# функция получения данных по погоде из прошлого спринта
# и запись их в файл в папку /cities/
def get_weather(city_name: str = 'MOSCOW'):

    logger.info('check folder cities')
    if not os.path.exists('./cities/'):
        os.makedirs('./cities/')

    yw_api = YandexWeatherAPI()

    try:
        logger.info('get response weather')
        response = yw_api.get_forecasting(city_name)
    except Exception as error:
        logger.error(f'error request weather: {error}')
    else:
        logger.info(f'create and write file {city_name}')
        with open(f'./cities/{city_name}.txt', 'w',
                  encoding='utf-8') as f:
            f.write(str(response))


# функция чтения файла из папки cities
def rd_file(city_name: str = 'MOSCOW'):
    logger.info(f'read file {city_name}')
    with open(f'./cities/{city_name}.txt', 'r') as file:
        for s in file:
            yield s


def load_api_MOSCOW():
    get_weather(city_name='MOSCOW')


def load_api_PARIS():
    get_weather(city_name='PARIS')


def load_api_LONDON():
    get_weather(city_name='LONDON')


def load_api_BERLIN():
    get_weather(city_name='BERLIN')


def read_file_MOSCOW():
    yield from rd_file(city_name='MOSCOW')


def read_file_PARIS():
    yield from rd_file(city_name='PARIS')


def read_file_LONDON():
    yield from rd_file(city_name='LONDON')


def read_file_BERLIN():
    yield from rd_file(city_name='BERLIN')
