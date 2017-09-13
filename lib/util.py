# -*- coding: utf-8-*-

import os
import sys
import logging
import yaml
import re

from lib.voice.baseVoice import AbstractVoiceEngine
import lib.appPath

def create_daemon(daemon_callback=None,args=()):
    '''
    创建守护进程，daemon_callback 为运行守护进程的函数, args为对应运行函数参数
    '''
    #产生子进程，而后父进程退出
    try:
        if os.fork() > 0:
            sys.exit(0)
    except OSError, error:
        print("fork #1 failed: %d (%s)"%(error.errno,error.strerror))
        sys.exit(1)

    #修改子进程工作目录
    os.chdir("/")
    #创建新的会话，子进程成为会话的首进程
    os.setsid()
    #修改工作目录的umask
    os.umask(0)

    #创建孙子进程，而后子进程退出
    try:
        pid = os.fork()
        if pid > 0:
            print('Daemon pid is %d' % pid)
            sys.exit(0)
    except OSError, error:
        print("fork #2 failed: %d (%s)"%(error.errno,error.strerror))
        sys.exit(1)

    #重定向标准输入流、标准输出流、标准错误
    sys.stdout.flush()
    sys.stderr.flush()
    si = file("/dev/null", 'r')
    so = file("/dev/null", 'a+')
    se = file("/dev/null", 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())
    
    daemon_callback(*args)


def filt_punctuation(text):
    """
    过滤中英文标点符号,返回unicode码
    """
    from zhon.hanzi import punctuation
    hanzi_punc = punctuation
    from string import punctuation
    en_punc = punctuation
    punctuation = hanzi_punc + en_punc

    try:
        res = re.sub(ur"[%s]+" %punctuation, "", text.decode("utf-8"))
    except UnicodeDecodeError:
        return ''

    return res

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
