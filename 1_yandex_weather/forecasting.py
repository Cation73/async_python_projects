import multiprocessing

from api_client import YandexWeatherAPI
from tasks import (
    DataFetchingTask,
    DataCalculationTask,
    DataAggregationTask,
    DataAnalyzingTask,
)
from utils import CITIES

path_folder = './data/'

def forecast_weather(path_folder):
    """
    Анализ погодных условий по городам
    """
    # заливка данных из API
    dft = DataFetchingTask(YandexWeatherAPI, CITIES, path_folder)
    dft.load_weather_data()
    # расчет средний значений
    dct = DataCalculationTask(path_folder, 9, 19)
    q = multiprocessing.Queue()
    dct.run_calc(q)
    # агрегация
    dat = DataAggregationTask(q, path_folder)
    aggreg_json = dat.aggregation_json()
    # финальный результат
    dant = DataAnalyzingTask(aggreg_json)
    result = dant.get_favourite_city()
    
    print(result)


if __name__ == "__main__":
    forecast_weather(path_folder)
