import unittest
import datetime
import warnings

from job import Job
from scheduler import Scheduler
from example_tasks import load_api_BERLIN
from utils import JobStatus

warnings.filterwarnings("ignore")


class TestCase(unittest.TestCase):
    # для проверки вызова классов
    def setUp(self):
        self.sched = Scheduler()
        self.job = Job(id='3bef0032-d2e6-4dd7-b571-9c4e88fbc337',
                       task=load_api_BERLIN,
                       args=[],
                       kwargs={},
                       start_at=datetime.datetime.now(),
                       max_working_time=-1,
                       tries=0,
                       dependencies=[]
                       )

    # проверка отработки функции на выполнение таски
    def test_chec_depend_task_complete(self):
        self.assertEqual(self.job.check_depend_task_complete(), True)

    # проверка вызова классов
    def test_is_instance(self):
        self.assertIsInstance(self.sched, Scheduler)
        self.assertIsInstance(self.job, Job)

    # проверка на ненулевой результат для получения параметров таски
    def test_job_get_params(self):
        list_message = self.job.__dict__
        self.assertIsNotNone(list_message)

    # проверка на ненулевой результат для функции получения данных из бэкапа
    def test_sched_restart_dict(self):
        list_message = self.sched.get_backup_tasks()
        self.assertIsNotNone(list_message)

    # проверка работы планировщика
    def test_schedule(self):
        self.sched.schedule(self.job)
        self.assertIn(self.job, self.sched.queue)

    # проверка работы создания задач внутри планировщика
    def test_get_task(self):
        self.sched.schedule(self.job)
        start_at = datetime.datetime.now()
        another_job = self.sched.get_task(id='123456-d2e6-4dd7-b571-'
                                          '9c4e88fbc337',
                                          task=load_api_BERLIN,
                                          args=[],
                                          kwargs={},
                                          start_at=start_at,
                                          status=JobStatus.queue,
                                          max_working_time=-1,
                                          tries=0,
                                          dependencies=[])

        self.assertEqual(another_job.id, '123456-d2e6-4dd7-b571-9c4e88fbc337')
        self.assertEqual(another_job.task, load_api_BERLIN)
        self.assertEqual(another_job.args, [])
        self.assertEqual(another_job.kwargs, {})
        self.assertEqual(another_job.start_at, start_at)
        self.assertEqual(another_job.status, JobStatus.queue)
        self.assertEqual(another_job.max_working_time, -1)
        self.assertEqual(another_job.tries, 0)
        self.assertEqual(another_job.dependencies, [])

    # проверка получения задачи по id
    def test_get_task_from_queue(self):
        self.sched.schedule(self.job)
        another_job = self.sched.get_task_from_queue(id='3bef0032-d2e6-4dd7-'
                                                     'b571-9c4e88fbc337')

        self.assertEqual(another_job.id, '3bef0032-d2e6-4dd7-b571-'
                         '9c4e88fbc337')


if __name__ == '__main__':
    unittest.main()
