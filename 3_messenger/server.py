from __future__ import annotations
import os
import json
import asyncio
import datetime as dt
from asyncio.streams import StreamReader, StreamWriter

from logger import logger
import utils


class Server:
    def __init__(self,
                 host: str = utils.DEFAULT_HOST,
                 port: int = utils.DEFAULT_PORT,
                 count_max_messages: int = utils.MAX_MESSAGE_COUNT,
                 message_live_time: dt.timedelta = utils.MESSAGE_LIVE_TIME,
                 users: dict = None,
                 bans_users: dict = None,
                 ban_count: int = utils.BAN_COUNT,
                 ban_seconds: int = utils.BAN_TIME,
                 name_chats: list = None,
                 messages_store: list = None,
                 dt_messages: list = None):

        self.host: str = host
        self.port: int = port
        self.count_max_messages: int = count_max_messages
        self.message_live_time: dt.timedelta = message_live_time
        self.users: dict = users or {}
        self.bans_users: dict = bans_users or {}
        self.ban_count: int = ban_count
        self.ban_seconds: int = ban_seconds
        self.name_chats: list = name_chats or []
        self.messages_store: list = messages_store or []
        self.dt_messages: list = dt_messages or []
        self.history: dict = {"general":
                              {"users": self.users,
                               "messages_store": self.messages_store,
                               "dt_messages": self.dt_messages}}

    # слушатель
    async def listen(self, reader: StreamReader, writer: StreamWriter):
        welcome_message = utils.LOGIN_MESSAGE
        writer.write(welcome_message.encode())
        await writer.drain()
        username = await reader.readline()
        username = username.decode().strip()
        logger.info(f"Start server - {username}")

        if self.check_exist_user(username):
            logger.warning(f"{username} did already find")
            await self.send_last_messages(writer)
        else:
            logger.info(f"Welcome new user - {username}")
            welcome_message = utils.LOGIN_MESSAGE + f'{username}'
            print(welcome_message)
            await self.send_public_message(welcome_message, username)
            await self.send_last_messages(writer)
   
        self.users[username] = writer

        try:
            while True:
                message = await reader.readline()

                # очистка старых сообщений
                list_index = [self.dt_messages.index(dtm)
                              for dtm in self.dt_messages
                              if dt.datetime.strptime(dtm, '%d.%m.%Y %H:%M:%S')
                              >= dt.datetime.now() - self.message_live_time]

                self.messages_store = [self.messages_store[idx]
                                       for idx in list_index]
                self.dt_messages = [self.dt_messages[idx]
                                    for idx in list_index]

                # проверка на бан
                if (username in self.bans_users.keys()
                        and self.bans_users[username] >= 3):
                    self.bans_users[username] = 0
                    await asyncio.sleep(self.ban_seconds)

                else:
                    if (not message) | (message.decode().startswith('/quit')):
                        logger.warning("Not message or quit from chat")
                        await self.stop()
                        writer.close()
                        break

                    elif message.decode().startswith('/get_chat'):
                        logger.info("Apply command /get_chat")
                        await self.get_chat(writer)
                        continue

                    elif message.decode().startswith('/chats'):
                        logger.info("Apply command /chats")
                        await self.chats(message, username, writer)
                        continue

                    elif message.decode().startswith('/send'):
                        logger.info("Apply command /send")
                        await self.send_private_message(message, username)
                        continue

                    elif message.decode().startswith('/ban'):
                        logger.info("Apply command /ban")
                        await self.get_ban(message, username)
                        continue

                    dt_message = dt.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
                    message = f"{dt_message} - {username}: {message.decode().strip()}\n"
                    self.messages_store.append(message)
                    self.dt_messages.append(dt_message)
                    logger.info(message)
                    await self.send_public_message(message, username)
        except Exception as error:
            logger.error(f"Error listening - {error}")
            writer.close()

    # запуск сервера
    async def start(self):
        try:
            logger.info("Start server")
            self.st_server = await asyncio.start_server(self.listen,
                                                        self.host,
                                                        self.port)
            async with self.st_server:
                await self.st_server.serve_forever()
        except Exception as error:
            logger.error(f"Don't start server - {error}")
            raise error

    # проверка на повторную авторизацию пользователя
    def check_exist_user(self, username: str) -> bool:
        for user in self.users.keys():
            if username == user:
                return True
        return False

    # отправка последнего сообщения
    async def send_last_messages(self,
                                 writer: StreamWriter) -> None:
        for message in self.messages_store[-self.count_max_messages:]:
            writer.write(f'{message}\n'.encode())
            await writer.drain()

    # отправка сообщения о том, что пользователь уже авторизирован
    async def send_found_message(self,
                                 username: str,
                                 writer: StreamWriter) -> None:
        try:
            dt_message = dt.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            message = f"{dt_message} - {username} was find in chat\n"
            writer.write(message.encode())
            await writer.drain()
        except Exception as error:
            logger.error(f"Error send found message - {error}")

    # отправка сообщения в канал
    async def send_public_message(self,
                                  message: str,
                                  writer: str) -> None:
        try:
            for user, writer_client in self.users.items():
                for _, chat in self.history.items():
                    if (user in chat['users']
                            and writer in chat['users']):
                        logger.info(f"send public message - {writer}")
                        writer_client.write(f"{message}\n".encode())
                        await writer_client.drain()
        except Exception as error:
            logger.error(f"Error send public message - {error}")

    # получение списка чатов
    async def get_chat(self, writer: StreamWriter):
        try:
            self.name_chats = [chat for chat in self.history.keys()]
            dt_message = dt.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            writer.write(f"{dt_message}"
                         f" - {str(self.name_chats)}\n".encode())
            await writer.drain()
        except Exception as error:
            logger.error(f"Error get chats - {error}")

    # создание нового чата или переход в существующий
    async def chats(self,
                    message: bytes,
                    username: str,
                    writer: StreamWriter) -> None:
        message = message.decode()
        name_chat = message.split()[1]
        self.name_chats = [chat for chat in self.history.keys()]

        if name_chat in self.name_chats:
            logger.info("Move to chat")
            chat = next(filter(lambda x: x.name == name_chat,
                               self.history.values()),
                        None)
        else:
            logger.info("Create new chat")

            self.history[name_chat] = {"users": {},
                                       "messages_store": [],
                                       "dt_messages": []}
            self.name_chats.append(name_chat)
            chat = {name_chat: {"users": {},
                                "messages_store": [],
                                "dt_messages": []}}

        if chat is not None:
            self.delete_user_from_chat(username)
            self.history[name_chat]["users"][username] = writer
            self.history[name_chat]["messages_store"] = self.messages_store
            self.history[name_chat]["dt_messages"] = self.dt_messages
            dt_message = dt.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            move_message = f"{dt_message} - You moved to {name_chat}\n"
            writer.write(move_message.encode())
            await writer.drain()

    # отправка сообщения в лс
    async def send_private_message(self, message: bytes, username: str) -> None:
        try:
            message = message.decode()
            client_name = message.split()[1]
            client_message = ' '.join(message.split()[2:])
            for user, writer_client in self.users.items():
                if user == client_name:
                    dt_message = dt.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
                    writer_client.write(f"{dt_message} - {username}:"
                                        f" {client_message}\n".encode())
                    await writer_client.drain()
        except Exception as error:
            logger.error(f"Error send private message - {error}")

    # обработка жалоб
    async def get_ban(self, message: bytes, username: str) -> None:
        login_ban = message.decode().split()[1]
        if login_ban not in self.users.keys():
            await self.send_private_message((f"/send {username}"
                                            " User was't find").encode(),
                                            'Admin')
        else:
            if login_ban not in self.bans_users.keys():
                self.bans_users[login_ban] = 0

            if self.bans_users[login_ban] < self.ban_count:
                self.bans_users[login_ban] += 1
            else:
                dt_message = dt.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
                ban_message = f"{dt_message} - Admin: {login_ban} is banned"
                self.messages_store.append(ban_message)
                self.dt_messages.append(dt_message)
                await self.send_public_message(ban_message, username)

    # удаление пользователя из чата
    def delete_user_from_chat(self, username: str) -> None:
        try:
            logger.info(f"Delete {username} from chat")
            for _, chat in self.history.items():
                if username in chat['users']:
                    chat['users'].pop(username)
        except Exception as error:
            logger.error(f"Error delete {username} from chat - {error}")

    # сохранение историчности чата
    async def stop(self) -> None:
        logger.info('Closing server and saving backup history messanger')
        self.st_server.close()
        await self.st_server.wait_closed()

        if os.path.exists("./backup/") is False:
            os.makedirs("./backup/")

        with open("./backup/backup_"
                  f"{dt.datetime.now().timestamp()}.json", "w",
                  encoding="utf-8") as file:
            json.dump(self.history, file, default=str)

        logger.info('Server stopped')
        logger.info('Done save history messanger')

    # восстановление бэкапа мессенджера
    def get_backup(self):
        try:
            logger.info('open json file with backup messanger')
            name_file = sorted(os.listdir('./backup/'))[-1]
            with open(f'./backup/{name_file}', 'r', encoding='utf-8') as file:
                self.history = json.load(file)

        except Exception as error:
            logger.error(f'error open json file: {error}')
            self.history = {}


server = Server()


async def main() -> None:
    logger.info("Start function main")
    await server.start()


async def backup() -> None:
    logger.info('Save backup')
    await server.stop()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.error("KeyboardInterrupt error")
        asyncio.run(backup())
    except SystemError:
        logger.error("SystemError error")
        asyncio.run(backup())
    except SystemExit:
        logger.error("SystemExit error")
        asyncio.run(backup())
    except asyncio.IncompleteReadError:
        logger.error("IncompleteReadError error")
        asyncio.run(backup())
