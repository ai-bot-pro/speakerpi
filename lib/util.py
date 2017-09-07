# -*- coding: utf-8-*-

import os
import logging
import yaml

from lib.voice.baseVoice import AbstractVoiceEngine
import lib.appPath

def init_logger(name=""):
    """
    初始日志
    """
    logger = logging.getLogger(name)

    config_path = os.path.join(lib.appPath.CONFIG_PATH, 'log.yml');
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            profile = yaml.safe_load(f)
            if 'level' in profile:
                logger.setLevel(eval("logging."+profile['level']))

    return logger


def get_subclasses(cls):
    """
    获取子类
    """
    subclasses = set()
    for subclass in cls.__subclasses__():
        subclasses.add(subclass)
        subclasses.update(get_subclasses(subclass))

    return subclasses

def get_engines_by_cate(cate='voice'):
    '''
    通过类型获取引擎list
    '''
    if cate is 'voice':
        return [engine for engine in
            list(get_subclasses(AbstractVoiceEngine))
            if hasattr(engine, 'TAG') and engine.TAG]

def get_engine_by_tag(tag=None,cate='voice'):
    """
    通过标签获取可用引擎
    没有引擎抛出异常
    """
    if not tag or type(tag) is not str:
        raise TypeError("Invalid engine tag '%s'", tag)

    selected_engines = filter(lambda engine: hasattr(engine, "TAG") and
                              engine.TAG == tag, get_engines_by_cate(cate))
    if len(selected_engines) == 0:
        raise ValueError("No STT engine found for tag '%s'" % tag)
    else:
        if len(selected_engines) > 1:
            print(("WARNING: Multiple STT engines found for tag '%s'. " +
                   "This is most certainly a bug.") % tag)
        engine = selected_engines[0]
        if not engine.is_available():
            raise ValueError(("STT engine '%s' is not available (due to " +
                              "missing dependencies, missing " +
                              "dependencies, etc.)") % tag)
        return engine
