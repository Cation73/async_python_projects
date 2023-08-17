import sys
import unittest
import multiprocessing

import warnings
warnings.filterwarnings("ignore")

from tasks import DataFetchingTask, DataCalculationTask, DataAggregationTask, DataAnalyzingTask
from api_test import check_api
from api_client import YandexWeatherAPI
from utils import CITIES

class TestCase(unittest.TestCase):
    # для проверки вызова классов
    def setUp(self):
        self.dft = DataFetchingTask(YandexWeatherAPI, CITIES, './data/')
        self.dct = DataCalculationTask('./data/')
        self.dat = DataAggregationTask(multiprocessing.Queue(), './data/')
        self.dant = DataAnalyzingTask({'Abu Dhabi': 
                                       {'Температура, среднее': {'2022-05-26': 34.8, '2022-05-27': 34.5, '2022-05-28': 33.8, '2022-05-29': 34.0, '2022-05-30': 'nan', 'Среднее': 34.275, 'Рейтинг': 15}, 
                                        'Без осадков, часов': {'2022-05-26': 11, '2022-05-27': 11, '2022-05-28': 11, '2022-05-29': 2, '2022-05-30': 0, 'Среднее': 7.0, 'Рейтинг': 13}}, 
                                      'Baoding District': {'Температура, среднее': {'2022-05-26': 31.8, '2022-05-27': 32.7, '2022-05-28': 33.8, '2022-05-29': 28.2, '2022-05-30': 'nan', 'Среднее': 31.625, 'Рейтинг': 13}, 
                                                           'Без осадков, часов': {'2022-05-26': 11, '2022-05-27': 11, '2022-05-28': 11, '2022-05-29': 6, '2022-05-30': 0, 'Среднее': 7.8, 'Рейтинг': 15}}})
    # тест функции загрузки данных по API
    def test_api(self):
        self.assertEqual(check_api(), True)
    
    # проверка вызова классов
    def test_is_instance(self):
        self.assertIsInstance(self.dft, DataFetchingTask)
        self.assertIsInstance(self.dct, DataCalculationTask)
        self.assertIsInstance(self.dat, DataAggregationTask)
        self.assertIsInstance(self.dant, DataAnalyzingTask)

    # проверка на ненулевой результат для функции загрузки по API
    def test_dft_is_not_none(self):
        list_message = self.dft.load_weather_data()
        self.assertIsNotNone(list_message)

    # проверка на ненулевой результат для функции расчета средних значений
    def test_dct_is_not_none(self):
        list_message = self.dct.calc_metrics('Moscow.json')
        self.assertIsNotNone(list_message)

    # проверка на ненулевой результат для функции агрегации
    def test_dat_is_not_none(self):
        list_message = self.dat.aggregation_json()
        self.assertIsNotNone(list_message)

    # проверка на ненулевой результат для функции выбора лучших городов
    def test_dant_is_not_none(self):
        list_message = self.dant.get_favourite_city()
        self.assertIsNotNone(list_message)


if __name__ == '__main__':
    unittest.main()