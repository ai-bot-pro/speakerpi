# -*- coding: utf-8-*-

import sys, os, time, random
import re

import yaml
import argparse
import logging
from multiprocessing import Process, Queue, Pipe
import psutil

from lib.voice.baiduVoice import BaiduVoice
from lib.voice.snowboyVoice import SnowboyVoice
from lib.mic import Mic,RawTextMic
import lib.appPath
import lib.util

from plugin.fm.doubanFM import DoubanFM
import plugin.fm.doubanFM
from lib.conversation import Conversation
from plugin.bootstrap import Bootstrap

import signal

interrupted = False

def signal_handler(signal, frame):
    global interrupted
    interrupted = True

def interrupt_callback():
    global interrupted
    return interrupted

# capture SIGINT signal, e.g., Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

def run(robot_name="ROBOT",logger=None,args=None):
    bootstrap_file = os.path.join(lib.appPath.CONFIG_PATH, 'bootstrap.yml')
    if os.path.exists(bootstrap_file) is False:
        logger.error("bootstrap file is not exists!")
        return False

    # Read config
    logger.debug("Trying to read config file: '%s'", bootstrap_file)
    try:
        with open(bootstrap_file, "r") as f:
            bootstrap_config = yaml.safe_load(f)
    except OSError:
        logger.error("Can't open config file: '%s'", bootstrap_file)
        raise
       
    #语音唤醒实例
    try:
        passive_stt_engine_tag = bootstrap_config['passive_stt_engine']
    except KeyError:
        passive_stt_engine_tag = 'snowboy'
        logger.warning("passive_stt_engine not specified in profile, defaulting " + "to '%s'", passive_stt_engine_tag)
    passive_stt_engine_class = lib.util.get_engine_by_tag(passive_stt_engine_tag)

    #语音识别实例
    try:
        active_stt_engine_tag = bootstrap_config['active_stt_engine']
    except KeyError:
        active_stt_engine_tag = 'baidu-ai-voice'
        logger.warning("active_stt_engine not specified in profile, defaulting " + "to '%s'", active_stt_engine_tag)
    active_stt_engine_class = lib.util.get_engine_by_tag(active_stt_engine_tag)

    #语音合成实例
    try:
        speak_engine_tag = bootstrap_config['speak_engine']
    except KeyError:
        speak_engine_tag = 'baidu-ai-voice'
        logger.warning("speak_engine not specified in profile, defaulting " + "to '%s'", speak_engine_tag)
    speak_engine_class = lib.util.get_engine_by_tag(speak_engine_tag)
    
    #语音录入实例
    mic = RawTextMic() if args.debug else Mic()
    
    #会话(指令)初始
    conversation = Conversation(robot_name, mic, 
            speak_engine_class.get_instance(), 
            active_stt_engine_class.get_instance(),
            passive_stt_engine_class.get_instance(),
            bootstrap_config)


    #开始交互
    conversation.handleForever(interrupt_check=interrupt_callback)

    #插件引导初始
    #bootstrap = Bootstrap(speak_engine_class.get_instance(), bootstrap_config)

    '''
    queue = Queue()
    conversation_process = Process(target=conversation.handleForever,args=(interrupt_callback,queue,))
    bootstrap_process = Process(target=bootstrap.query,args=(queue,))
    conversation_process.start()
    bootstrap_process.start()
    conversation_process.join()
    bootstrap_process.join()
    '''

def debugDoubanFm(logger=None,args=None):
    baidu_voice = BaiduVoice.get_instance()

    out_pipe, in_pipe = Pipe(True)
    
    son_p = Process(target=Bootstrap.son_process, 
                args=(baidu_voice, (out_pipe, in_pipe),
                plugin.fm.doubanFM.son_process_handle))

    son_p.start()

    # 等pipe被fork 后，关闭主进程的输出端; 创建的Pipe一端连接着主进程的输入，一端连接着子进程的输出口
    out_pipe.close()

    debug_words = [
            u"播放豆瓣电台",
            #u"下一首", 
            #u"暂停",
            #u"继续播放",
            #u"喜欢这首歌",
            #u"不喜欢这首歌",
            #u"删除这首歌",
            #u"不再播放这首歌",
            #u"下载",
            #u"下载这首歌",
            #u"结束豆瓣电台",
        ]

    for text in debug_words:
        is_valid = plugin.fm.doubanFM.isValid(text)
        if is_valid is True:
            plugin.fm.doubanFM.send_handle(text,in_pipe,son_p)
        else:
            print("word %s is not valid" % text)

    in_pipe.close()
    son_p.join()
    print "debug doubanFM son process with pipe is over"


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='doubanFM pi')
    parser.add_argument('--debug', action='store_true',
                        help='Show debug messages')
    parser.add_argument('--debugDoubanFmPlugin', action='store_true',
                        help='Show debug douban fm plugin messages')
    args = parser.parse_args()
    
    logging.basicConfig(stream=sys.stdout)
    logger = logging.getLogger("")
    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.debugDoubanFmPlugin:
        debugDoubanFm(logger,args)
    else:
        run('weedge',logger,args)



