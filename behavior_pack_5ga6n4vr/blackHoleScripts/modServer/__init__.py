# -*- coding: utf-8 -*-
import logging
import sys


def make_server_logger():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] [blackHole Server] %(message)s'))
    lg = logging.getLogger('blackHoleServerLogger')
    lg.handlers = []
    lg.addHandler(handler)
    lg.propagate = False
    return lg


logger = make_server_logger()
