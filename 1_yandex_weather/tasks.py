import json
import os
import math
import time
import multiprocessing 
import numpy as np 
from concurrent.futures import ThreadPoolExecutor, as_completed

import warnings
warnings.filterwarnings("ignore")

from api_client import YandexWeatherAPI
from logger import logger
from utils import CITIES


# скачивание данных по API
class DataFetchingTask:
    # инициализация 
    def __init__(self,
                 yw_api: YandexWeatherAPI,
                 cities: CITIES,
                 path_folder: str) -> None:
        
        self._yw_api = yw_api()
        self._cities = cities
        self._path_folder = path_folder

    # определение функции загрузки данных по API Яндекс.Погода
    def load_weather_data(self) -> list:
        logger.info("-- run load_weather_data")
        try:
            # создание потоков
            with ThreadPoolExecutor() as executor:
                logger.info("-- generate threads")
                futures = [executor.submit(self.yw_api.get_forecasting, city_name) for city_name in self._cities.keys()]
                
                # сохранение название скаченных файлов для дальнейшего переиспользования
                list_city_names = []

                # получение результата запросов по API
                for task in as_completed(futures):
                    logger.info("-- get result load_weather_data")

                    city_name = task.result()['geo_object']['locality']['name']

                    self.save_to_json(city_name, task.result())

                    list_city_names.append(city_name)
                        
                logger.info(f"- return list_city_names")       
                return list_city_names         
        except Exception as error:
            logger.error(error)

    # сохранение файлов
    def save_to_json(self,
                     city_name: str,
                     task_result: dict) -> None:

        with open(f"{self._path_folder}{city_name}.json", "w") as file_json:
            logger.info(f"-- save file - {city_name.encode('utf-8')}")
            json.dump(task_result, file_json)
        
# расчет средней температуры и осадков - подготовка данных к агрегации
class DataCalculationTask:
    # инициализация 
    def __init__(self,
                 path_folder: str,
                 left_threshold_hour: int,
                 right_threshold_hour: int) -> None:
        
        self._path_folder = path_folder
        self.left_threshold_hour = left_threshold_hour
        self.right_threshold_hour = right_threshold_hour

    # расчет средней температуры и кол-во часов без осадков
    def calc_metrics(self,
                    name_city: str) -> dict:    
    
        dict_city = dict()

        logger.info(f"- open file with data of {name_city.encode('utf-8')}")
        with open(f'{self._path_folder}{name_city}') as f:
            j = json.load(f)
            city = j['geo_object']['locality']['name']
            dict_city[city] = dict()
            j = j['forecasts']
            logger.info(f"-- calculate metrics to {name_city.encode('utf-8')}")
            for day in range(len(j)):
                dict_city[city][j[day]['date']] = dict() 

                logger.info(f"-- calculate mean temperature to {name_city.encode('utf-8')}")
                dict_city[city][j[day]['date']]['temp'] = np.round(np.mean([int(j[day]['hours'][hour]['temp']) for hour in range(len(j[day]['hours'])) \
                                                            if (int(j[day]['hours'][hour]['hour'])>=self.left_threshold_hour) & (int(j[day]['hours'][hour]['hour'])<=self.right_threshold_hour)]), 1)

                logger.info(f"-- calculate count good conditions to {name_city.encode('utf-8')}")
                dict_city[city][j[day]['date']]['condition'] = len([j[day]['hours'][hour]['condition'] for hour in range(len(j[day]['hours'])) \
                                                            if (int(j[day]['hours'][hour]['hour'])>=self.left_threshold_hour) & (int(j[day]['hours'][hour]['hour'])<=self.right_threshold_hour) & \
                                                                (j[day]['hours'][hour]['condition'] in ('cloudy', 'clear', 'partly-cloudy', 'overcast'))])

        logger.info(f"- return dict {name_city.encode('utf-8')}")

        return dict_city
        
    # использование параллельного подхода - отправление данных в очередь
    def run_calc(self, queue: multiprocessing.Queue) -> None:
        logger.info(f"-- get names json files")
        list_names_city = os.listdir(self._path_folder)

        processes = multiprocessing.cpu_count() - 1
        
        logger.info(f"-- run calc_metrics with Pool")
        with multiprocessing.Pool(processes=processes) as p:
            for result in p.map(self.calc_metrics, list_names_city):
                logger.info(f"-- put element to queue")
                queue.put(result)
                time.sleep(1)

# агрегация данных, формирование рейтинга
class DataAggregationTask:
    # инициализация 
    def __init__(self,
                 queue: multiprocessing.Queue,
                 path_folder: str) -> None:
        self.queue = queue
        self._path_folder = path_folder

    # получение элементов из очереди
    def get_queue_items(self) -> dict:
        
        while True:
            if self.queue.empty():
                logger.info(f"-- Queue is empty")
                break
            else:
                logger.info(f"-- get element from queue")
                item = self.queue.get()
                time.sleep(1)
                return item
            
    # преобразование данных к json
    def aggregation_json(self) -> dict:

        list_names_city = os.listdir(self._path_folder)
        list_names_city = [city.replace('.json', '') for city in list_names_city]

        dict_city = dict()
        logger.info(f"-- Iterate get item from queue")
        for idx, val in enumerate(list_names_city):  
            try:
                item = self.get_queue_items()

                k = list(item.keys())[0]
                logger.info(f"-- get {k.encode('utf-8')}")

                dict_city[k] = dict()
                dict_city[k]['Температура, среднее'] = dict()
                dict_city[k]['Без осадков, часов'] = dict()

                logger.info(f"-- calculate mean metrics {k.encode('utf-8')}")
                for k1, v1 in item[k].items():
                    dict_city[k]['Температура, среднее'][k1] = v1['temp']
                    dict_city[k]['Без осадков, часов'][k1] = v1['condition']
            
                dict_city[k]['Температура, среднее']['Среднее'] = np.mean([temp for temp in dict_city[k]['Температура, среднее'].values() if not math.isnan(temp)])
                dict_city[k]['Без осадков, часов']['Среднее'] = np.mean([cond for cond in dict_city[k]['Без осадков, часов'].values() if cond != ''])
            except Exception as error:
                logger.error(f"error in get queue - {error}")

        logger.info(f"-- calculate temperature rating") 
        sort_temp = sorted(dict_city, key = lambda x: dict_city[x]['Температура, среднее']['Среднее'])
        for idx, val in enumerate(sort_temp):
            dict_city[val]['Температура, среднее']['Рейтинг'] = idx+1

        logger.info(f"-- calculate condition rating") 
        sort_cond = sorted(dict_city, key = lambda x: dict_city[x]['Без осадков, часов']['Среднее'])
        for idx, val in enumerate(sort_cond):
            dict_city[val]['Без осадков, часов']['Рейтинг'] = idx+1
        

        return dict_city
    
class DataAnalyzingTask:
    # инициализация 
    def __init__(self,
                 json_file: dict) -> None:
        super().__init__()
        self.json_file = json_file

    # вывод максимально благоприятных городов
    def get_favourite_city(self) -> list:
        list_rating = []
        dict_fav_city = dict()
        logger.info(f"-- calculate sum rating city")
        for k, v in self.json_file.items():
            dict_fav_city[k] = dict()

            dict_fav_city[k]['Сумма рейтингов'] = v['Температура, среднее']['Рейтинг'] + v['Без осадков, часов']['Рейтинг']

            list_rating.append(dict_fav_city[k]['Сумма рейтингов'])

        logger.info(f"-- sorted and return list with top cities")
        sort_city = sorted(dict_fav_city, key = lambda x: dict_fav_city[x]['Сумма рейтингов'], reverse=True)
        list_fav_city = []
        for city in sort_city[:list_rating.count(max(list_rating))]:
            self.json_file[city]['Рейтинг'] = 1
            list_fav_city.append((city, self.json_file[city]))

        return list_fav_city

