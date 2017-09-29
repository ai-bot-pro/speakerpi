# -*- coding: utf-8-*-
import sys, os, time, random
import re
import json
import argparse
import logging
import psutil
from multiprocessing import Process, Queue, Pipe

from lib.graphic.baiduGraphic import BaiduGraphic
from lib.voice.baiduVoice import BaiduVoice
from lib.voice.baseVoice import AbstractVoiceEngine
from plugin.bootstrap import Bootstrap
import lib.appPath
import lib.util
import plugin.volume.pulseAudio 
from plugin.fm.doubanFM import DoubanFM
from lib.mail import SMTPMail
from plugin.monitor.people import PeopleMonitor

def doubanFM(logger,args):
    speaker = BaiduVoice.get_instance()
    douban_fm = DoubanFM.get_instance()
    douban_fm.set_speaker(speaker)
    for i in range(0,2):
        song = douban_fm.playRandomLikeSong()
    

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
            u"声音小点", 
            u"声音再小一点", 
            u"声音大点",
            u"声音再大一点", 
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

def mail(logger,args):
    smtpMail = SMTPMail.get_instance()
    with open('./mind-idea.jpg', 'rb') as f:
        smtpMail.sendImageEmail(f.read())

    logger.debug("debug mail is over")

def peopleMonitor(logger,args):
    speaker = BaiduVoice.get_instance()
    people_monitor = PeopleMonitor.get_instance()
    people_monitor.set_speaker(speaker)

    def get_text_callback():
        index = random.choice([0,1])
        test_words = [
                u'打开人体监控',
                u'结束人体监控',
            ]
        logger.debug("index %d, text:%s",index,test_words[index])
        time.sleep(5)
        return test_words[index]
    people_monitor.start(get_text_callback)

    logger.debug("debug peopleMonitor is over")

def baiduGraphic(logger,args):
    def get_file_content(filePath):
        with open(filePath, 'rb') as fp:
            return fp.read()
    baidu_graphic = BaiduGraphic.get_instance()

    for detect_type in ["plant","dish","car","logo","animal","object","face"]:
        file = os.path.join(lib.appPath.APP_PATH, '.'.join([detect_type,'jpg']))
        img = get_file_content(file)
        res = baidu_graphic.detectImage(img,detect_type)
        logger.debug("%s: %s",detect_type,json.dumps(res,encoding="UTF-8",ensure_ascii=False))

    logger.debug("debug baiduGraphic is over")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='debug')
    parser.add_argument('--debug', action='store_true',
                        help='Show debug messages')
    parser.add_argument('--pulseAudio', action='store_true',
                        help='Show debug pulse audio plugin messages')
    parser.add_argument('--doubanFM', action='store_true',
                        help='Show debug douban fm plugin messages')
    parser.add_argument('--mail', action='store_true',
                        help='Show debug mail lib messages')
    parser.add_argument('--peopleMonitor', action='store_true',
                        help='Show debug people monitor plugin messages')
    parser.add_argument('--baiduGraphic', action='store_true',
                        help='Show debug baidu graphic lib messages')

    args = parser.parse_args()
    logging.basicConfig(stream=sys.stdout)
    logger = logging.getLogger("")
    if args.debug:
        logger.setLevel(logging.DEBUG)
    if args.pulseAudio:
        pulseAudio(logger,args)
        exit(0)

    if args.doubanFM:
        doubanFM(logger,args)
        exit(0)

    if args.mail:
        mail(logger,args)
        exit(0)

    if args.peopleMonitor:
        peopleMonitor(logger,args)
        exit(0)

    if args.baiduGraphic:
        baiduGraphic(logger,args)
        exit(0)
