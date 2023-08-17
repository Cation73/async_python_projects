import asyncio
from concurrent.futures import ThreadPoolExecutor

from logger import logger
import utils


class Client:
    def __init__(self,
                 username: str,
                 server_host: str = utils.DEFAULT_HOST,
                 server_port: int = utils.DEFAULT_PORT):

        self.username = username
        self.server_host = server_host
        self.server_port = server_port

    @staticmethod
    async def ainput(message: str = "\n") -> str:
        with ThreadPoolExecutor(1, 'ainput') as executor:
            return (await asyncio.get_event_loop()
                    .run_in_executor(executor,
                                     input,
                                     message)).rstrip()

    # соединение пользователя с сервером
    async def start(self) -> None:
        logger.info(f"Start Client - {self.username}")
        try:
            self.reader, \
                self.writer = await asyncio.open_connection(self.server_host,
                                                            self.server_port)
            logger.info(f"Connected to {self.server_host}:{self.server_port}")
            print(f"Connected to {self.server_host}:{self.server_port}")

            self.writer.write(f"{self.username}\n".encode())
            await asyncio.gather(self.send(), self.read())

        except Exception as error:
            logger.error(f"Error start connect client to server: {error}")

    # отправка сообщения пользователем
    async def send(self) -> None:
        while True:
            try:
                message = await self.ainput()
                logger.info(f"{self.username} send message: {message}")
                await asyncio.sleep(0.1)
                self.writer.write(f"{message}\n".encode())
                await self.writer.drain()
            except Exception as error:
                logger.error(f"Error send message to server: {error}")

    # чтение сообщения пользователем
    async def read(self) -> None:
        while True:
            try:
                message = await self.reader.readline()
                if not message:
                    break
                else:
                    message = message.decode().strip()
                logger.info(f"read message: {message}")
                await asyncio.sleep(0.1)
            except Exception as error:
                logger.error(f"Error read message to server: {error}")


async def main() -> None:
    client = Client(username=str(input()))
    await client.start()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Client is disabled')
