import logging
import datetime
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s'
                              ' - %(message)s')

if os.path.exists('./logs/') is False:
    os.makedirs('./logs/')

file_handler = logging.FileHandler(f'./logs/messanger_'
                                   f'{str(datetime.datetime.now().date())}'
                                   '.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
