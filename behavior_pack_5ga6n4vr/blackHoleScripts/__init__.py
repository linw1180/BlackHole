import logging
import sys


def make_main_logger():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] [blackHole Main] %(message)s'))
    lg = logging.getLogger('blackHoleMainLogger')
    lg.handlers = []
    lg.addHandler(handler)
    lg.propagate = False
    return lg


logger = make_main_logger()
