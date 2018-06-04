import logging
import os
from os.path import expanduser

def setup_custom_logger(name):
    #logging.getLogger('urllib3').setLevel(logging.WARNING)
    #logging.getLogger('requests').setLevel(logging.WARNING)
    #logging.getLogger('chardet').setLevel(logging.WARNING)
    
    #dir = expanduser('~')
    dir = os.path.dirname(os.path.abspath(__file__))
    fn = os.path.join(dir, 'configs/sunray.log')
    formatter = logging.Formatter(fmt='%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.FileHandler(fn, mode='a',encoding = 'UTF-8')
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger
