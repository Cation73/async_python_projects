import unittest
import warnings
from asyncio.streams import StreamWriter

from server import Server
from client import Client

warnings.filterwarnings("ignore")


class TestCase(unittest.IsolatedAsyncioTestCase):
    # для проверки вызова классов
    def setUp(self):
        self.server = Server(users={"Vadim": "connect", "Bob": "connect1"},
                             name_chats=["general"],
                             messages_store=["14.05.2023 11:28:12 - Vadim: Ho",
                                             "14.05.2023 11:28:36 - Vadim: kak"
                                             ],
                             dt_messages=["14.05.2023 11:28:12",
                                          "14.05.2023 11:28:36"])
        self.client = Client()

    # проверка вызова классов
    def test_class_is_instance(self):
        self.assertIsInstance(self.server, Server)
        self.assertIsInstance(self.client, Client)

    # проверка функции поиска пользователей
    def test_exists_user(self):
        self.assertTrue(self.server.check_exist_user('Vadim'))

    # проверка отправки получения списка чатов
    async def test_get_chat(self):
        await self.server.get_chat(writer=StreamWriter)

    # проверка функции удаления пользователей из чата
    def test_del_users(self):
        self.server.delete_user_from_chat('Bob')
        self.assertEqual(list(self.server.__dict__['users'].keys())[0],
                         'Vadim')

    async def test_connect_server(self):
        pass

    async def test_connect_client(self):
        pass


if __name__ == '__main__':
    unittest.main()
