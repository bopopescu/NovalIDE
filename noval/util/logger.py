#----------------------------------------------------------------------------
# Name:         logger.py
# Purpose:      Utilities to help with logging
#
# Author:       Jeff Norton
#
# Created:      01/04/05
# CVS-ID:       $Id$
# Copyright:    (c) 2005 novalide, Inc.
# License:      wxWindows License
#----------------------------------------------------------------------------
import logging
import sys

LEVEL_FATAL = logging.FATAL
LEVEL_ERROR = logging.ERROR
LEVEL_WARN = logging.WARN
LEVEL_INFO = logging.INFO
LEVEL_DEBUG = logging.DEBUG

loggingInitialized = False

NORMAL_IDE_LOG_NAME = "noval.ide"
DEBUG_IDE_LOG_NAME = "noval.debug"
DEFAULT_IDE_LOG_NAME = NORMAL_IDE_LOG_NAME

def initLogging(is_debug=False, force=False):
    global default_ide_logger, loggingInitialized,DEBUG_IDE_LOG_NAME,DEFAULT_IDE_LOG_NAME,NORMAL_IDE_LOG_NAME
    if (force or not loggingInitialized):
        loggingInitialized = True
        configFile = None
        log_level = logging.INFO
        defaultStream = sys.stdout
        if is_debug:
            log_level = logging.DEBUG
            DEFAULT_IDE_LOG_NAME = DEBUG_IDE_LOG_NAME
            defaultStream = sys.stderr
        handler = logging.StreamHandler(defaultStream)
        handler.setLevel(log_level)
        handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s"))
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(log_level)
        default_ide_logger = logging.getLogger(DEFAULT_IDE_LOG_NAME)
        default_ide_logger.setLevel(log_level)
    
default_ide_logger = logging.getLogger(DEFAULT_IDE_LOG_NAME)

def get_logger(logger_name = ""):
    if logger_name == "" or logger_name == "root":
        return default_ide_logger
    return logging.getLogger(logger_name)

