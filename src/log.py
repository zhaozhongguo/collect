import logging
import sys
import os

LOG_FILENAME = os.path.join(sys.path[0], "../log/collect.log")

logging.basicConfig(level=logging.INFO,
            format='%(asctime)s [%(process)d] %(filename)s[line:%(lineno)d] [%(funcName)s] %(levelname)s %(message)s',
            datefmt='%Y%m%d %H:%M:%S',
            filename=LOG_FILENAME,
            filemode='w')