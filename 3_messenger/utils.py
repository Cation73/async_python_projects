import datetime

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8000
MAX_MESSAGE_COUNT = 20
MESSAGE_LIVE_TIME = datetime.timedelta(minutes=60)

LOGIN_MESSAGE = ('Welcome to chat! First, you need to login. '
                 'Enter username: ')

BAN_TIME = datetime.timedelta(hours=4).total_seconds()
BAN_COUNT = 3
