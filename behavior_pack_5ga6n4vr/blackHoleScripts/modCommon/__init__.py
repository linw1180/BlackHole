# -*- coding: utf-8 -*-
import logging
import sys


def make_common_logger():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] [blackHole Common] %(message)s'))
    lg = logging.getLogger('blackHoleCommonLogger')
    lg.handlers = []
    lg.addHandler(handler)
    lg.propagate = False
    return lg


logger = make_common_logger()