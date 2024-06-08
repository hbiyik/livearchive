'''
Created on Jun 7, 2024

@author: boogie
'''
import logging

logger = logging.getLogger('log')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)10s | %(filename)15s | %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

debug = logging.DEBUG
info = logging.INFO


def setlevel(level):
    logger.setLevel(level)
    ch.setLevel(level)
