import logging
import os
from datetime import datetime

from pytz import utc, timezone


def setup_logger():
    # Get today's date in the desired format
    KST = timezone('Asia/Seoul')

    today = datetime.now()
    today = utc.localize(today).astimezone(KST)
    today = today.strftime('%Y%m%d')

    # Create a directory for today's date if it doesn't exist
    log_directory = './logs'
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # Define the log file name
    log_filename = os.path.join(log_directory, f'{today}.log')
    # Create a logger
    logger = logging.getLogger('MyDailyLogger')
    logger.setLevel(logging.INFO)  # Set the logging level

    # Create a file handler for logging
    file_handler = logging.FileHandler(log_filename)
    formatter = logging.Formatter(u'%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    return logger
