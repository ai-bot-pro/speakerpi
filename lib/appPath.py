# -*- coding: utf-8-*-
import os

APP_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))

CONFIG_PATH = os.path.join(APP_PATH, "conf")
DATA_PATH = os.path.join(APP_PATH, "data")
LOG_PATH = os.path.join(APP_PATH, "log")
LIB_PATH = os.path.join(APP_PATH, "lib")
PLUGIN_PATH = os.path.join(APP_PATH, "plugin")

def config(*fname):
    return os.path.join(CONFIG_PATH, *fname)

def data(*fname):
    return os.path.join(DATA_PATH, *fname)
