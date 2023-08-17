import datetime
from typing import Callable, Any

from utils import JobStatus
from logger import logger


class Job:
    def __init__(self,
                 id: str,
                 task: Callable,
                 args: list = None,
                 kwargs: dict = None,
                 status=JobStatus(0),
                 start_at: datetime = datetime.datetime.now(),
                 max_working_time: int = -1,
                 tries: int = 0,
                 dependencies: list = None):

        self.id = id
        self.task = task
        self.task_name = task.__name__
        self.args = args or []
        self.kwargs = kwargs or {}
        self.status = status
        self.start_at = start_at
        self.max_working_time = max_working_time
        self.tries = tries
        self.dependencies = dependencies or []

        self.step = datetime.timedelta(seconds=10)
        self.end_at = datetime.datetime.now()

    # запуск job
    def run(self) -> None:
        logger.info('run task')
        try:
            self.task(*self.args, **self.kwargs)
            self.end_at = datetime.datetime.now()
        except Exception as error:
            logger.error(f'error run task: {error}')
            return None

    # проверка зависимых задач на выполнение
    def check_depend_task_complete(self) -> bool:
        logger.info('check dependencies tasks completed')
        for task in self.dependencies:
            if task.status == JobStatus.completed:
                continue
            else:
                logger.warning(f'task {self.task_name} is not completed')
                return False
        logger.info('all dependencies tasks completed')
        return True

    # опытным путем было выявлено, что без этой функции
    # невозможно отсортировать задачи в очереди
    def __lt__(self, another: Any) -> bool:
        if another.status.value != self.status.value:
            return another.status.value > self.status.value
        return another.start_at > self.start_at

    # функция проверки на то, что зависимые функции запустились раннее
    def check_depend_task_start_dt(self) -> None:
        logger.info('check dependencies tasks start datetime')
        for task in self.dependencies:
            if task.start_at > self.start_at:
                self.start_at = task.end_at + datetime.timedelta(seconds=5)

    # функция для получения следующего времени запуска
    def set_next_dt(self) -> None:
        self.start_at += self.step
