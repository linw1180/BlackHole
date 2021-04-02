# -*- coding: utf-8 -*-
import logging
import sys


def make_client_logger():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] [blackHole Client] %(message)s'))
    lg = logging.getLogger('blackHoleClientLogger')
    lg.handlers = []
    lg.addHandler(handler)
    lg.propagate = False
    return lg


logger = make_client_logger()