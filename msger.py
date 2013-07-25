#!/usr/bin/python -tt
# vim: sw=4 ts=4 sts=4 et ai

import os
import sys
import logging

__all__ = ['set_msger', 'debug', 'info', 'warning', 
           'error', 'critical', 'exception']

# Color escape string
COLOR_RED='\033[1;31m'
COLOR_GREEN='\033[1;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_BLUE='\033[1;34m'
COLOR_PURPLE='\033[1;35m'
COLOR_CYAN='\033[1;36m'
COLOR_GRAY='\033[1;37m'
COLOR_WHITE='\033[1;38m'
COLOR_RESET='\033[1;0m'
 
# Define msg color
LOG_COLORS = {
    'DEBUG': '%s',
    'INFO': '%s',
    #'INFO': COLOR_GREEN + '%s' + COLOR_RESET,
    'WARNING': COLOR_YELLOW + '%s' + COLOR_RESET,
    'ERROR': COLOR_RED + '%s' + COLOR_RESET,
    'CRITICAL': COLOR_RED + '%s' + COLOR_RESET,
    'EXCEPTION': COLOR_RED + '%s' + COLOR_RESET,
}

class ColoredFormatter(logging.Formatter):
    '''A colorful formatter'''
    def __init__(self, fmt=None, datefmt=None):
        logging.Formatter.__init__(self, fmt, datefmt)
 
    def format(self, record):
        level = record.levelname
        msg = logging.Formatter.format(self, record)
 
        return LOG_COLORS.get(level, '%s') % msg

def import_funcs():
    global g_msger
    curr_module = sys.modules[__name__]
    func_names = ['debug', 'info', 'warning', 'error', 'critical', 'exception']

    for func_name in func_names:
        func = getattr(g_msger, func_name)
        setattr(curr_module, func_name, func)

def set_msger(stream_name=None, stream_level='INFO', 
              file_name=None, file_level='DEBUG'):
    global g_msger 
    if not g_msger: g_msger = logging.getLogger()
    logging.shutdown()
    g_msger.handlers = []
    g_msger.setLevel(logging.DEBUG)

    if not stream_name: stream_name = sys.stdout
    stream_level = getattr(logging, stream_level, logging.INFO)
    stream_formatter = ColoredFormatter('')
    stream_handler = logging.StreamHandler(stream_name)
    stream_handler.setLevel(stream_level)
    stream_handler.setFormatter(stream_formatter)

    if not file_name: file_name = str(os.getpid())
    file_level = getattr(logging, file_level, logging.DEBUG)
    file_formatter = logging.Formatter('')
    file_handler = logging.FileHandler(file_name)
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)

    g_msger.addHandler(stream_handler)
    g_msger.addHandler(file_handler)

    import_funcs()

# Global msger
g_msger= None

# Set a default msger
set_msger()
