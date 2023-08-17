import datetime
import uuid
from typing import Callable

from job import Job
from scheduler import Scheduler
import example_tasks


list_cities = ['MOSCOW', 'PARIS', 'LONDON', 'BERLIN']


# получение функции из строки
def call_method(cls: Callable, name_function: str):
    return getattr(cls, name_function)


# функция генерации задач
def generate_tasks(scheduler: Scheduler):

    for i in range(len(list_cities)):
        job_load = Job(id=str(uuid.uuid4()),
                       task=call_method(example_tasks,
                                        f'load_api_{list_cities[i]}'),
                       args=[],
                       kwargs={},
                       start_at=datetime.datetime.now())

        scheduler.schedule(job_load)

        job_read = Job(id=str(uuid.uuid4()),
                       task=call_method(example_tasks,
                                        f'read_file_{list_cities[i]}'),
                       args=[],
                       kwargs={},
                       start_at=datetime.datetime.now())

        scheduler.schedule(job_read)
    scheduler.run()


if __name__ == "__main__":
    scheduler = Scheduler()
    generate_tasks(scheduler)
    # scheduler.restart()
