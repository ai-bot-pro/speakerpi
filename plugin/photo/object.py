#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import time
import re

import lib.appPath
from lib.graphic.baiduGraphic import BaiduGraphic
from lib.camera import PhotographCamera

TAG = 'object'
CATE = 'photo'

def son_process_handle(speaker,get_text_callback):
    '''
    子进程处理逻辑
    speaker: voice实例(tts)
    get_text_callback: 获取文本指令回调函数
    '''
    print("<<<<<<< begin photo object son process handle >>>>>>>")

def send_handle(text,in_fp,son_processor,speaker):
    '''
    发送指令给子进程处理(pipe,signal)
    text: 指令
    in_fp: pipe 输入端
    son_processor: 子进程(Process 实例)
    speaker: voice实例(tts)
    '''
    print("<<<<<<< begin photo object send pipe handle >>>>>>>")
    baidu_graphic = BaiduGraphic.get_instance()
    detect_type = None
    if re.search(u'菜品', text): detect_type = "dish"
    if re.search(u'车', text): detect_type = "car"
    if re.search(u'植物', text): detect_type = "plant"
    if re.search(u'动物', text): detect_type = "animal"
    if re.search(u'标志', text): detect_type = "logo"

    pid_file = os.path.join(lib.appPath.DATA_PATH, "monitor"+"_"+__name__+'.pid');
    monitor_pid_cmd = " ".join(["find",lib.appPath.DATA_PATH,"-type f -name  monitor_*.pid"])
    monitor_pid = os.popen(monitor_pid_cmd).readline()
    if(monitor_pid == ""):
        #拍照
        img = PhotographCamera.photographToBytesIO()
        #识别
        res = baidu_graphic.detectImage(img,detect_type) if detect_type is not None else None

        name = res['name'] if 'name' in res else None
        if name is not None:
            speaker.say("这个应该是"+name.encode("UTF-8"))
        else:
            speaker.say("没有识别出来，请放好点再试一次吧")
    else:
        speaker.say("正在监控中，请关了监控然后再试试吧")

    in_fp.close()
    son_processor.join()
    pid_file = os.path.join(lib.appPath.DATA_PATH, CATE+"_"+__name__+'.pid');
    if os.path.exists(pid_file):
        os.remove(pid_file)

def isValid(text):
    valid_words = [
            u"这是什么菜品",
            u"这是什么车",
            u"这是什么植物",
            u"这是什么动物",
            u"这是什么标志",
        ]
    res = any(word in text for word in valid_words)
    return res

