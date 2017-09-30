# -*- coding: utf-8-*-
import re
import os
import sys
import time
import threading

import logging
import yaml
from flask import Flask, render_template, Response
import cv2

import lib.appPath
from lib.baseClass import AbstractClass
from lib.mail import SMTPMail
from lib.camera import VideoCamera

TAG = 'people'
CATE = 'monitor'

def son_process_handle(speaker,get_text_callback):
    '''
    子进程处理逻辑
    speaker: voice实例(tts)
    get_text_callback: 获取文本指令回调函数
    '''
    print("<<<<<<< begin monitor people son process handle >>>>>>>")
    speaker.say('开始人体监控')
    people_monitor = PeopleMonitor.get_instance()
    people_monitor.set_speaker(speaker)
    people_monitor.start(get_text_callback=get_text_callback)

def send_handle(text,in_fp,son_processor,speaker):
    '''
    发送指令给子进程处理(pipe,signal)
    text: 指令
    in_fp: pipe 输入端
    son_processor: 子进程(Process 实例)
    speaker: voice实例(tts)
    '''
    print("<<<<<<< begin monitor people send pipe handle >>>>>>>")

    if all(word not in text for word in [u'打开人体监控',u'开始人体监控']):
        print("send valid word %s to pipe" % text.encode("UTF-8"))
        in_fp.send(text)

    if re.search(u'结束人体监控', text) or re.search(u'关闭人体监控', text):
        in_fp.close()
        son_processor.join()
        pid_file = os.path.join(lib.appPath.DATA_PATH, CATE+"_"+__name__+'.pid');
        if os.path.exists(pid_file):
            os.remove(pid_file)
        speaker.say(text.encode("UTF-8")+"已经处理")

def isValid(text):
    valid_words = [
            u"开始人体监控",
            u"打开人体监控",
            u"结束人体监控",
            u"关闭人体监控",
        ]
    res = any(word in text for word in valid_words)
    return res

class PeopleMonitor(AbstractClass):

    @classmethod
    def is_available(cls):
        return (super(cls, cls).is_available() and
                lib.diagnose.check_executable('opencv_createsamples') and
                lib.diagnose.check_executable('opencv_traincascade') and
                lib.diagnose.check_executable('opencv_waldboost_detector'))

    def __init__(self,opencv_cascade_classifier,body_part="face",email_update_interval=300):
        super(self.__class__, self).__init__()
        self.object_email = SMTPMail.get_instance()
        self.email_update_interval = email_update_interval
        self.video_camera = VideoCamera(flip=False)

        model_file = os.path.join(lib.appPath.APP_PATH,opencv_cascade_classifier[body_part]);
        self.object_classifier = None
        if os.path.exists(model_file):
            self.object_classifier = cv2.CascadeClassifier(model_file)
        self.speaker = None

    @classmethod
    def get_config(cls):
        config = {}
        config_path = os.path.join(lib.appPath.CONFIG_PATH, 'monitor.yml')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                profile = yaml.safe_load(f)
                if 'people' in profile:
                    people_config = profile['people']
                    if 'body_part' in people_config:
                        config['body_part'] = people_config['body_part']
                    if 'email_update_interval' in people_config:
                        config['email_update_interval'] = people_config['email_update_interval']
                    if 'opencv_cascade_classifier' in people_config:
                        config['opencv_cascade_classifier'] = people_config['opencv_cascade_classifier']

        return config

    def set_speaker(self,speaker):
        self.speaker = speaker

    def start(self,get_text_callback=None):
        last_epoch = 0
        self._logger.debug("monitor people start")
        while True:
            if (get_text_callback is not None):
                try:
                    text = get_text_callback()
                    if text is not None:
                        self._logger.debug("-----got text %s from pipe------",text)
                        command = self.dispatch_command_callback(text)
                        if command == "exit": 
                            self.video_camera.stop()
                            break

                    frame, found_obj = self.video_camera.get_object(self.object_classifier)
                    if found_obj and (time.time() - last_epoch) > self.email_update_interval:
                        last_epoch = time.time()
                        self._logger.debug("Sending email...at %d",last_epoch)
                        self.object_email.sendImageEmail(frame)
                        self.speaker.say("刚才我发送了一封监控邮件给您，请注意查收")
                        self._logger.debug("Send email is ok!")
                except:
                    self._logger.debug("People Monitor Error : %s", sys.exc_info()[0])
                    break

    def dispatch_command_callback(self,text):
        command = 'p'
        if re.search(u'结束人体监控', text): command = "exit"
        if re.search(u'关闭豆瓣电台', text): command = "exit"
        return command
