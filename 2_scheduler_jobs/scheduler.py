import os
import datetime
import json
from typing import List, Callable
from time import sleep

from job import Job
from utils import coroutine, JobStatus
from logger import logger
import example_tasks


class Scheduler:
    def __init__(self,
                 pool_size: int = 10):

        self.pool_size: int = pool_size
        self.queue: List[Job] = []
        self.run_schedule: bool = False

    # получение задачи
    def get_task(self,
                 id: str,
                 task: Callable,
                 args: list,
                 kwargs: dict,
                 status: JobStatus,
                 start_at: datetime,
                 max_working_time: int,
                 tries: int,
                 dependencies: list[Job]) -> Job:

        logger.info('get task from queue')
        current_task = self.get_task_from_queue(id)

        if current_task:
            logger.info('return task')
            return current_task
        else:
            logger.warning('create new task')
            current_task = Job(id=id,
                               task=task,
                               args=args,
                               kwargs=kwargs,
                               status=JobStatus.queue
                               if status == JobStatus.progress else status,
                               start_at=start_at,
                               max_working_time=max_working_time,
                               tries=tries,
                               dependencies=dependencies)

            return current_task

    # получение задачи из очереди
    def get_task_from_queue(self, id: str) -> Job:
        logger.info('get task from queue')
        try:
            task = next(t for t in self.queue if t.id == id)
        except StopIteration:
            logger.warning('task was not found in queue')
            task = None

        return task

    # добавление задачи в scheduler
    def schedule(self, task: Job) -> None:

        logger.info('add task in list tasks')
        if self.get_task_from_queue(task.id):
            logger.debug('task was added later')

        logger.info('check dependencies tasks')
        if task.dependencies:
            for depend_task in task.dependencies:
                if depend_task not in self.queue:
                    self.schedule(depend_task)

        self.queue.append(task)
        logger.info('task was added in queue of scheduler')

    # основная логика запуска задач в scheduler
    def _process_scheduler(self, task):
        logger.info('run process scheduler')
        if task is not None:
            while self.run_schedule:
                self.queue.sort()
                if (self.queue[0].status == JobStatus.queue) & \
                        (len(self.queue) > 0):

                    time_run_next_task = self.queue[0].start_at.timestamp() - \
                        datetime.datetime.now().timestamp()

                    if time_run_next_task > 0:
                        logger.warning('task waiting')
                        sleep(time_run_next_task)
                    else:
                        logger.info('task ready')

                    if self.queue[0].check_depend_task_complete() is False:
                        logger.warning('dependencies tasks are not ready')
                        self.queue[0].set_next_dt()
                    else:
                        logger.info('dependencies tasks are ready')

                    if len([t for t in self.queue if t.status == JobStatus.
                            progress]) < self.pool_size:
                        logger.info('task change status to progress')
                        self.queue[0].status = JobStatus.progress
                        task.send(self.queue[0])
                    else:
                        logger.warning('pool size more than 10 tasks')
                else:
                    self.run_schedule = False
                    logger.warning('the scheduler is finished working')

    # вызов задачи
    @coroutine
    def _process_task(self) -> None:
        while task := (yield):
            try:
                task.result = task.run()
                task.status = JobStatus.completed
            except Exception as error:
                logger.error(f'task {task.task_name} is error: {error}')

                if task.tries > 0:
                    task.next_start()
                    task.tries -= 1
                    task.status = JobStatus.queue
                else:
                    task.status = JobStatus.error

    # запуск задачи
    def run(self):

        logger.info('run scheduler')
        self.run_schedule = True

        try:
            task = self._process_task()

            self._process_scheduler(task)
        except KeyboardInterrupt:
            logger.warning('KeyboardInterrupt: accident stopping process - \
                           save backup')
            self.stop()
        except SystemExit:
            logger.warning('KeyboardInterrupt: accident stopping process - \
                           save backup')
            self.stop()
        except SystemError:
            logger.warning('KeyboardInterrupt: accident stopping process - \
                           save backup')
            self.stop()

    # сбор данных перед остановкой
    def collection_tasks(self) -> list | None:
        logger.info('run stopping scheduler')
        self.run_schedule = False

        tasks = []
        try:
            for task in self.queue:
                task_dict = task.__dict__
                task_dict.pop('task', None)
                task_dict['status'] = task.status.value
                task_dict['dependencies'] = [task_depend.__dict__
                                             for task_depend
                                             in task_dict['dependencies']]
                tasks.append(task_dict)
            return tasks
        except Exception as error:
            logger.error(f'error generate history tasks: {error}')
            return None

    # остановка scheduler
    def stop(self):
        logger.info('save history tasks in json')
        tasks = self.collection_tasks()

        if os.path.exists('./backup/') is False:
            os.makedirs('./backup/')

        with open(f'./backup/backup_ \
                  {datetime.datetime.now().timestamp()}.json', 'w',
                  encoding='utf-8') as file:
            json.dump(tasks, file, default=str)

        logger.info('scheduler stop')

    # получение backup данных
    @staticmethod
    def get_backup_tasks():
        try:
            logger.info('open json file with backup tasks')
            name_file = sorted(os.listdir('./backup/'))[-1]
            with open(f'./backup/{name_file}', 'r', encoding='utf-8') as file:
                tasks = json.load(file)
                return tasks
        except Exception as error:
            logger.error(f'error open json file: {error}')
            return None

    # получение функции из строки
    @staticmethod
    def call_method(cls: Callable, name_function: str):
        return getattr(cls, name_function)

    # рестарт scheduler
    def restart(self) -> None:

        tasks = self.get_backup_tasks()
        if tasks is not None:
            for task in tasks:

                dependencies = []

                for depend_task in task['dependencies']:
                    dependencies.append(
                        self.get_task(id=depend_task['id'],
                                      task=depend_task["task_name"],
                                      args=depend_task['args'],
                                      kwargs=depend_task['kwargs'],
                                      status=JobStatus(depend_task['status']),
                                      start_at=datetime.datetime.
                                      strptime(depend_task['start_at'],
                                               '%Y-%m-%d %H:%M:%S.%f'),
                                      max_working_time=depend_task
                                      ['max_working_time'],
                                      tries=depend_task['tries'],
                                      dependencies=depend_task['dependencies']
                                      ))

                job = self.get_task(id=task['id'],
                                    task=self.call_method(example_tasks,
                                                          task['task_name']),
                                    args=task['args'],
                                    kwargs=task['kwargs'],
                                    status=JobStatus(task['status']),
                                    start_at=datetime.datetime.strptime(
                                    task['start_at'],
                                    '%Y-%m-%d %H:%M:%S.%f'),
                                    max_working_time=task['max_working_time'],
                                    tries=task['tries'],
                                    dependencies=dependencies)

                self.schedule(job)
            self.run()
