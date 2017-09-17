# -*- coding: utf-8-*-
import sys, os, time, random
import re
import argparse
import logging
import psutil
from multiprocessing import Process, Queue, Pipe

from lib.voice.baiduVoice import BaiduVoice
from plugin.bootstrap import Bootstrap
import lib.appPath
import lib.util
import plugin.volume.pulseAudio 

def pulseAudio(logger,args):
    baidu_voice = BaiduVoice.get_instance()

    out_pipe, in_pipe = Pipe(True)
    
    son_p = Process(target=Bootstrap.son_process, 
                args=(baidu_voice, (out_pipe, in_pipe),
                plugin.volume.pulseAudio.son_process_handle,False))

    son_p.start()
    # 等pipe被fork 后，关闭主进程的输出端; 创建的Pipe一端连接着主进程的输入，一端连接着子进程的输出口
    out_pipe.close()

    words = [
            u"打开声音",
            u"声音小一点", 
            u"声音小一点", 
            u"声音大一点",
            u"静音",
            u"打开声音",
            u"安静",
            u"打开声音",
            #u"声音放到最大",
        ]

    for text in words:
        is_valid = plugin.volume.pulseAudio.isValid(text)
        if is_valid is True:
            logger.debug("word %s is valid" % text)
            plugin.volume.pulseAudio.send_handle(text,in_pipe,son_p,baidu_voice)
            time.sleep(3)
        else:
            logger.debug("word %s is not valid" % text)

    in_pipe.close()
    son_p.join()

    logger.debug("debug pulseAudio is over")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='debug')
    parser.add_argument('--debug', action='store_true',
                        help='Show debug messages')
    parser.add_argument('--pulseAudio', action='store_true',
                        help='Show debug douban fm plugin messages')

    args = parser.parse_args()
    logging.basicConfig(stream=sys.stdout)
    logger = logging.getLogger("")
    if args.debug:
        logger.setLevel(logging.DEBUG)
    if args.pulseAudio:
        pulseAudio(logger,args)

