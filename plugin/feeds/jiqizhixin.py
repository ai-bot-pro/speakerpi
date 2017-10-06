#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import time
import re
import requests
from HTMLParser import HTMLParser
import yaml
import json

import lib.appPath
import lib.diagnose
import lib.util
from lib.baseClass import AbstractClass

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

TAG = 'jiqizhixin'
CATE = 'feeds'

def son_process_handle(speaker,get_text_callback):
    '''
    发送指令给子进程处理(pipe,signal)
    text: 指令
    in_fp: pipe 输入端
    son_processor: 子进程(Process 实例)
    speaker: voice实例(tts)
    '''
    print("<<<<<<< begin jiqizhixin feeds send pipe handle >>>>>>>")
    speaker.say('开始阅读机器之心新闻')
    jqzx_feeds = JiqizhixinFeed.get_instance()
    jqzx_feeds.set_speaker(speaker)
    jqzx_feeds.start(get_text_callback=get_text_callback,command_callback=dispatch_command_callback)

def send_handle(text,in_fp,son_processor,speaker):
    '''
    发送指令给子进程处理(pipe,signal)
    text: 指令
    in_fp: pipe 输入端
    son_processor: 子进程(Process 实例)
    speaker: voice实例(tts)
    '''
    print("<<<<<<< begin jiqizhixin feeds send pipe handle >>>>>>>")

    if all(word not in text for word in [u'阅读机器之心',]):
        print("send valid word %s to pipe" % text.encode("UTF-8"))
        in_fp.send(text)

    if (re.search(u'下一条', text)):
        speaker.kill_play_procsss("_".join([CATE,TAG]))
        speaker.say(text.encode("UTF-8")+"操作成功")
        time.sleep(3)

    if re.search(u'结束阅读', text) or re.search(u'关闭阅读', text):
        speaker.kill_play_procsss("_".join([CATE,TAG]))
        in_fp.close()
        son_processor.join()
        pid_file = os.path.join(lib.appPath.DATA_PATH, CATE+"_"+__name__+'.pid');
        if os.path.exists(pid_file):
            os.remove(pid_file)
        speaker.say(text.encode("UTF-8")+"已经处理")


def isValid(text):
    valid_words = [
            u"阅读机器之心新闻",
            u"阅读机器之心摘要",
            u"阅读下一条",
            u"下一条",
            u"更新新闻",
            u"结束阅读",
            u"关闭阅读",
        ]
    res = any(word in text for word in valid_words)
    return res

def dispatch_command_callback(text):
    command = 'p'
    if re.search(u'阅读机器之心', text): command = "p"
    if re.search(u'下一条', text): command = "s"
    if re.search(u'更新', text): command = "update"
    if re.search(u'摘要', text): command = "digest"
    if re.search(u'结束', text): command = "exit"
    if re.search(u'关闭', text): command = "exit"

    return command

class MLStripper(HTMLParser):
    """
    strip html filt, extends HTMLParser
    """
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ' '.join(self.fed)

class JiqizhixinFeed(AbstractClass):
    '''
    采集机器之心的rss,获取feeds (PS:如果采集的rss.xml文件很大(1G+),建议先异步离线保存到本地,然后通过游标(iter)的形式读取)
    '''
    def __init__(self,rss_url="",digest='yes'):
        super(self.__class__, self).__init__()
        self.session = requests.Session()
        self.rss_url = rss_url
        self.offset = 0
        self.feeds = []
        self.simple = True if digest=="yes" else False
        self._get_feeds()

    @classmethod
    def get_config(cls):
        config = {}
        config_path = os.path.join(lib.appPath.CONFIG_PATH, 'feed.yml');
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                profile = yaml.safe_load(f)
                if 'jiqizhixin' in profile:
                    feed_config = profile['jiqizhixin']
                    if 'rss_url' in feed_config:
                        config['rss_url'] = feed_config['rss_url']
        return config

    def is_available(cls):
        return (super(cls, cls).is_available() and
                lib.diagnose.check_network_connection('www.jiqizhixin.com'))

    def set_speaker(self,speaker):
        self.speaker = speaker

    def _get_cdata(self,phase,filt_punctuation=False):
        rgx = re.compile("\<\!\[CDATA\[(.*?)\]\]\>")
        r = rgx.search(phase.replace('\n',''))
        if r is not None:
            stripper = MLStripper()
            stripper.feed(r.group(1))
            phase = stripper.get_data()
            phase = lib.util.filt_punctuation(phase.encode("UTF-8")) if filt_punctuation is True else phase

        return phase

    def get_feeds_count(self):
        return len(self.feeds)

    def _get_feeds(self):
        res = self.session.get(self.rss_url)
        xml = ET.fromstring(res.text.encode('UTF-8'))
        index = 0
        for item in xml.iter("item"):
            #notice: append/pop 操作对象的引用地址，每次都要新建一个feed，不然操作的是同一个feed对象
            feed = {}
            feed['title'] = item.find('title').text
            description = item.find('description').text
            feed['description'] = self._get_cdata(description)
            feed['author'] = item.find('author').text
            feed['pubDate'] = item.find('pubDate').text
            content_ns = "{http://purl.org/rss/1.0/modules/content/}"
            content = item.find(content_ns+'encoded').text
            feed['content'] = self._get_cdata(content)

            #self._logger.debug('feed in %s : %s', "_".join([CATE,TAG]),feed['title'])
            self.feeds.append(feed)

        return True

    def check_feeds(self):
        #offset: 必须大于0,从feeds头开始偏移,默认为第一篇
        if(self.offset<=0 or len(self.feeds)<self.offset):
            return False
        return True


    def _get_feed_to_speak(self):
        if(self.check_feeds() is False):
            return False
        one_feed = self.feeds[self.offset-1]
        title = one_feed['title'] if 'title' in one_feed else ''
        description = one_feed['description'] if 'description' in one_feed else ''
        pubDate = one_feed['pubDate'] if 'pubDate' in one_feed else ''
        at = time.mktime(time.strptime(pubDate,"%a, %d %b %Y %H:%M:%S +0800"))
        pubDate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(at))
        author = one_feed['author'] if 'author' in one_feed else ''
        
        if self.simple is True:
            #say_text = "".join([u"文章标题:",title,u";发布于:",pubDate,u";作者:",author,u";摘要如下:",description])
            say_text = "".join([description])
            self.speaker.say(say_text,"_".join([CATE,TAG]))
            return True
        else:
            say_text = "".join([u"文章标题:",title,u";发布于:",pubDate,u";作者:",author,u";摘要如下:",description,u";正文如下:"])
            self.speaker.say(say_text,"_".join([CATE,TAG]))

        split_phases = one_feed['content'].split(" ") if 'content' in one_feed else []
        text_len = 0
        speak_texts = []
        ct = 0
        for text in split_phases:
            text_len = text_len + len(text) + 1
            #超出512个字符(这里一个汉字算一个),调用speaker to say
            if text_len>512:
                speak_text = " ".join(speak_texts)
                self.speaker.say(speak_text,"_".join([CATE,TAG]))
                text_len = 0
                speak_texts = []
                ct = ct+1
            speak_texts.append(text)
        #最后一段话
        speak_text = " ".join(speak_texts)
        self.speaker.say(speak_text,"_".join([CATE,self.TAG]))

        self._logger.debug("speaker say count："+str(ct+1))

        return True

    def get_next_feed(self):
        if(len(self.feeds)<self.offset):
            return False
        self._logger.debug("get next feed %d",self.offset+1)
        self.offset = self.offset + 1
        return self._get_feed_to_speak()

    def get_next_action_feed(self):
        if(len(self.feeds)<self.offset):
            return False
        self.offset = self.offset + 1
        return self._get_feed_to_speak()

    def update_feeds(self):
        self.offset = 0
        self.feeds = []
        return self._get_feeds()

    def start(self, get_text_callback,command_callback=None):
        self._logger.debug("jiqizhixin feeds start")
        while True:
            if (command_callback is not None and get_text_callback is not None):
                try:
                    text = get_text_callback()
                    if text is not None:
                        self._logger.debug("-----got text %s from pipe------",text)
                        command = command_callback(text)
                        if (command=='exit'):
                            self._logger.debug("douban fm break")
                            break
                except EOFError:
                    # 当out_fd接受不到输出的时候且输入被关闭的时候，会抛出EORFError，可以捕获并且播放下首
                    self._logger.debug("-----no instructions in pipe or pipe is close,break polling------")
                    break

                if text is None:
                    self.get_next_feed()
                    continue

                operator = {
                    "p": self.get_next_feed,
                    "s": self.get_next_action_feed,
                    "update": self.update_feeds,
                }
                if operator.has_key(command):
                    operator[command]()

        self._logger.debug("jiqizhixin feeds over")
    
