# -*- coding: utf-8-*-

import os
import sys
import json
import re
import time
import pickle
import urllib,urllib2
import requests
import requests.utils
import psutil

import yaml

import lib.appPath
from baseFM import AbstractFM
from lib.voice.baiduVoice import BaiduVoice

from lib.gpio.manager import Manager as gpioManager

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

TAG = 'douban'
CATE = 'fm'

def dispatch_command_callback(text):
    global interrupted
    command = 'p'
    if re.search(u'播放豆瓣电台', text): command = "p"
    if re.search(u'下一首', text): command = "s"
    if re.search(u'喜欢', text): command = "r"
    if re.search(u'不喜欢', text): command = "u"
    if re.search(u'删除', text): command = "b"
    if re.search(u'不再播放', text): command = "b"
    if re.search(u'暂停', text): command = "stop"
    if re.search(u'继续播放', text): command = "continue"
    if re.search(u'结束豆瓣电台', text): command = "exit"
    return command

def son_process_handle(speaker,get_text_callback):
    '''
    子进程处理逻辑
    speaker: voice实例(tts)
    get_text_callback: 获取文本指令回调函数
    '''
    print("<<<<<<< begin douban fm son process handle >>>>>>>")
    douban_fm = DoubanFM.get_instance()
    douban_fm.set_speaker(speaker)
    douban_fm.start(get_text_callback=get_text_callback,
            interrupt_check=interrupt_callback,
            play_command_callback=dispatch_command_callback,
            sleep_time=0.05)

def send_handle(text,in_fp,son_processor,speaker):
    '''
    发送指令给子进程处理(pipe,signal)
    text: 指令
    in_fp: pipe 输入端
    son_processor: 子进程(Process 实例)
    speaker: voice实例(tts)
    '''
    print("<<<<<<< begin douban fm send pipe handle >>>>>>>")
    if all(word not in text for word in [u'暂停',u'继续播放']):
        print("send valid word %s to pipe" % text)
        in_fp.send(text)
    #父进程调用系统发信号给子进程
    if re.search(u'下一首', text) or re.search(u'删除', text) or re.search(u'不再播放', text):
        DoubanFM.kill_mplay_procsss()
        gpioManager.kill_procsss(TAG)
        time.sleep(3)
    if re.search(u'暂停', text):
        DoubanFM.suspend_mplay_process()
        gpioManager.suspend_process(TAG)
        speaker.say(text)
        time.sleep(1)
    if re.search(u'继续播放', text):
        DoubanFM.resume_mplay_process()
        gpioManager.resume_process(TAG)
        speaker.say(text)
        time.sleep(1)
    if re.search(u'结束豆瓣电台', text):
        DoubanFM.kill_mplay_procsss()
        gpioManager.kill_procsss(TAG)
        in_fp.close()
        #相当于执行os.waitpid(son_processor.pid)等待资源回收
        son_processor.join()
        pid_file = os.path.join(lib.appPath.DATA_PATH, __name__+'.pid');
        if os.path.exists(pid_file):
            os.remove(pid_file)

def isValid(text):
    global interrupted
    valid_words = [
            u"播放豆瓣电台",
            u"下一首", 
            u"暂停",
            u"播放",
            u"喜欢这首歌",
            u"不喜欢这首歌",
            u"删除这首歌",
            u"不再播放这首歌",
            u"下载",
            u"下载这首歌",
            u"结束豆瓣电台",
        ]

    res = any(word in text for word in valid_words)
    if res is True: interrupted = False
    return res


class DoubanFM(AbstractFM):

    def is_available(cls):
        return (super(cls, cls).is_available() and
                lib.diagnose.check_network_connection('www.douban.com'))

    def set_speaker(self,speaker):
        self.speaker = speaker

    def __init__(self, account_id, password, douban_id=None, robot_open_shake_bling="no",
            cookie_file=os.path.join(lib.appPath.DATA_PATH, 'douban_cookie.txt'),
            cur_song_file=os.path.join(lib.appPath.DATA_PATH, 'douban_cur_song.txt')):
        super(self.__class__, self).__init__()
        self.robot_open_shake_bling = robot_open_shake_bling
        self.ck = None
        self._mplay_process = None
        self._song = {}
        self._cur_song_file = cur_song_file
        self.douban_id = douban_id
        self.cookie_file = cookie_file
        self.data = {
            "form_email": account_id,
            "form_password": password,
            "source": "index_nav",
            "remember": "on"
        }
        self.session = requests.Session()
        self.login_url = 'https://www.douban.com/accounts/login'
        self.session.headers = {
            "User-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
            "Origin": "https://www.douban.com",
        }
        if self.load_cookies():
            self.get_ck()
        else:
            self.get_new_cookies()

    @classmethod
    def get_config(cls):
        config = {}
        config_path = os.path.join(lib.appPath.CONFIG_PATH, 'douban.yml');
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                profile = yaml.safe_load(f)
                if 'fm' in profile:
                    fm_config = profile['fm']
                    if 'account_id' in fm_config:
                        config['account_id'] = fm_config['account_id']
                    if 'password' in fm_config:
                        config['password'] = fm_config['password']
                    if 'douban_id' in fm_config:
                        config['douban_id'] = fm_config['douban_id']
                    if 'robot_open_shake_bling' in fm_config:
                        config['robot_open_shake_bling'] = fm_config['robot_open_shake_bling']
        return config

    def load_cookies(self):
        '''
        load cookies from file.
        '''
        try:
            with open(self.cookie_file) as f:
                self.session.cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
            return True
        except Exception, e:
            self._logger.error('faild to load cookies from file.')
            return False

    def get_new_cookies(self):
        if self.login():
            self.get_ck()

    def save_cookies(self, cookies):
        '''
        save cookies to file.
        '''
        if cookies:
            self.session.cookies.update(cookies)
        with open(self.cookie_file, 'w') as f:
            pickle.dump(requests.utils.dict_from_cookiejar(self.session.cookies), f)
        self._logger.debug('save cookies to file.')

    def get_ck(self):
        '''
        open douban.com and then get the ck from html.
        '''
        # r = self.session.get('http://httpbin.org/get',)
        r = self.session.get('https://www.douban.com/accounts/',cookies=self.session.cookies.get_dict())
        # save_html('1.html', r.text)
        cookies = self.session.cookies.get_dict()
        headers = dict(r.headers)
        if headers.has_key('Set-Cookie'):
            self._logger.debug('cookies is end of date, login again')
            self.ck = None
            self.get_new_cookies()
        elif cookies.has_key('ck'):
            self.ck = cookies['ck'].strip('"')
            self._logger.info("ck:%s" %self.ck)
        else:
            self._logger.error('cannot get the ck. ')

    def login(self):
        '''
        login douban.com and save the cookies to file.
        '''
        self.session.cookies.clear()
        # url = 'http://httpbin.org/post'  
        r = self.session.post(self.login_url, data=self.data, cookies=self.session.cookies.get_dict())
        html =  r.text
        # save_html('1.html', html)
        # 验证码
        regex = r'<img id="captcha_image" src="(.+?)" alt="captcha"'
        imgurl = re.compile(regex).findall(html)
        if imgurl:
            self._logger.info("The captcha_image url address is %s" %imgurl[0])
            captcha = re.search('<input type="hidden" name="captcha-id" value="(.+?)"/>', html)
            if captcha:
                # @todo: 引入文字识别，如果识别不成功，发送验证图片到手机微信/百度（通过消息上行接口实现），然后语音输入
                vcode=raw_input('图片上的验证码是：')
                self.data["captcha-solution"] = vcode
                self.data["captcha-id"] = captcha.group(1)
                self.data["user_login"] = "登录"
                # print 'yes'

            r = self.session.post(self.login_url, data=self.data, cookies=self.session.cookies.get_dict())
            # save_html('2.html',r.text)
        if r.url == 'https://www.douban.com/':
            self.save_cookies(r.cookies)
            self._logger.info('login successfully!')
        else:
            self._logger.error('Faild to login, check username and password and captcha code.')
            return False
        return True

    def getRecentChannels(self):
        """
        获取最近听过的电台频道
        """
        url = "https://douban.fm/j/v2/rec_channels?specific=all"
        payloads = { }
        response = self.session.get(url, params=payloads, cookies=self.session.cookies.get_dict())
        res = json.loads(response.text)

        return res
    
    def getRecentPlaySource(self):
        """
        获取最近听过的播放资源
        """
        url = "https://douban.fm/j/v2/recent_playsource"
        payloads = { }
        response = self.session.get(url, params=payloads, cookies=self.session.cookies.get_dict())
        res = json.loads(response.text)

        return res


    def getSong(self,type='p',sid=None,channel=0):
        """
        @brief
            获取私人电台当前播放歌曲信息 
        @params
            type: 获取类型, 默认p
                n:开始 p: 自然播放下首 s: 下首触发 r: 喜欢推荐触发 u: 不喜欢触发 b: 删除不在播放触发 (n,p应该是纯播放，未有人为操作)
            sid: 当前播放歌曲id, 默认为None
                这个应该是用来定义推荐歌手系类别(喜欢某个sid，会推荐相似sid的歌曲,咦~推荐系统)
            channel: 播放频道,默认0
        @return 
            dict 歌曲信息 or None
        """
        url = "https://douban.fm/j/v2/playlist?"
        payloads = {
            "channel":channel,#初始频道为0
            "kbps":192,
            "client":"s:mainsite|y:3.0",
            "app_name":"radio_website",
            "version":100,
            "type":type,
        }
        if (sid is not None) or (type=='n'):
            payloads_song = {
                "sid":sid,
                "pt":"126199.74799999999",#未知，可以为空
                "pb":128,
                "apikey":"",
            }
            payloads = dict(payloads,**payloads_song)

        self._logger.debug("get song url: %s,params: %s",url,payloads)
        response = self.session.get(url, params=payloads, cookies=self.session.cookies.get_dict())
        res = json.loads(response.text)
        song = None
        if('song' in res):
            song = self._song = res['song'][0]
            with open(self._cur_song_file, 'w') as f:
                pickle.dump(json.dumps(song), f)

        return song

    def _getSidFromLocal(self):
        '''
        从本地文件获取sid
        '''
        sid = None
        if os.path.exists(self._cur_song_file):
            with open(self._cur_song_file, 'r') as f:
                song = json.loads(pickle.load(f))
                if 'sid' in song:
                    sid = song['sid']

        return sid

    def playNextLikeSong(self):
        self._logger.debug("douban fm play next like song")
        self._mplay_process.wait()
        sid = self._getSidFromLocal()
        self.getSong(type='r',sid=sid)
        self.playSong()

    def playNextUnLikeSong(self):
        self._logger.debug("douban fm play next unlike song")
        self._mplay_process.wait()
        sid = self._getSidFromLocal()
        self.getSong(type='u',sid=sid)
        self.playSong()

    def playNextBanSong(self):
        self._logger.debug("douban fm play next ban song")
        '''
        if self._mplay_process is not None and self._mplay_process.pid>0:
            #已经在父进程通过信号结束了self._mplay_process.pid,子进程还保留这份数据，所以无需在执行
            pass
            self._mplay_process.kill()
        '''
        sid = self._getSidFromLocal()
        self.getSong(type='b',sid=sid)
        self.playSong()

    def playNextActionSong(self):
        self._logger.debug("douban fm play next action song")
        '''
        if self._mplay_process is not None and self._mplay_process.pid>0:
            #已经在父进程通过信号结束了self._mplay_process.pid,子进程还保留这份数据，所以无需在执行
            pass
            self._mplay_process.kill()
        '''
        sid = self._getSidFromLocal()
        self.getSong(type='s',sid=sid)
        self.playSong()

    def playNextSong(self):
        '''
        自然播放到下首歌
        '''
        sid = self._getSidFromLocal()
        type = 'p'
        if sid is None:#最开始,未有播放记录
            type='n'
        self.getSong(type=type,sid=sid)
        self.playSong()
        
    def stopSong(self):
        """
        暂停播放当前歌曲
        """
        res = None
        self._logger.debug("douban fm stop playing song")
        '''
        if self._mplay_process is not None and self._mplay_process.pid>0:
            self._logger.debug("pid: %d",self._mplay_process.pid)
            res = psutil.Process(self._mplay_process.pid).suspend()
        '''

        return res
    
    def continue2PlaySong(self):
        """
        继续播放当前歌曲
        """
        res = None
        self._logger.debug("douban fm continue to play song")
        '''
        if self._mplay_process is not None and self._mplay_process.pid>0:
            self._logger.debug("pid: %d",self._mplay_process.pid)
            res = psutil.Process(self._mplay_process.pid).resume()
        '''
        return res

    def playSong(self):
        song = self._song
        if song is not None:
            try:
                albumtitle = song['albumtitle'].encode('UTF-8')
                url = song['url'].encode('UTF-8')
                title = song['title'].encode('UTF-8')
                artist = song['artist'].encode('UTF-8')
                region = song['singers'][0]['region'][0].encode('UTF-8')
                song_length = song['length']
                singer_info = "歌曲" + title + "来自专辑" + albumtitle + "由" + region +"歌手" + artist + "演唱"

                if(self.robot_open_shake_bling=="yes"):
                    #边说,边dong
                    gpioManager.shakeshake(
                                son_process_callback=self.speaker.say,
                                process_args=(singer_info,),
                                shake_num=1)
                else:
                    self.speaker.say(singer_info)

                if(self.robot_open_shake_bling=="yes"):
                    #边播，边bling
                    gpioManager.shakeshake_blingbling(TAG,process_callback=self.mplay,
                                    process_args=(url,),
                                    shake_num=0,bling_num=song_length)
                else:
                    self.mplay(url)
            except IndexError:
                self._logger.error("播放%s 失败",url)
                pass

    def start(self, get_text_callback, play_command_callback=None,
              interrupt_check=lambda: False,
              sleep_time=0.03):
        
        self._logger.debug("douban fm start")
        while True:
            if (play_command_callback is not None 
                    and get_text_callback is not None):
                try:
                    self._logger.debug("-----start get text from pipe------")
                    text = get_text_callback()
                    if text is not None:
                        self._logger.debug("-----got text %s from pipe------",text)
                except EOFError:
                    # 当out_fd接受不到输出的时候且输入被关闭的时候，会抛出EORFError，可以捕获并且播放下首
                    self._logger.debug("-----no instructions in pipe or pipe is close,break douban fm polling------")
                    break

                #未收到任何指令，继续自然の播放
                if (text is None):
                    self.playNextSong()
                    continue

                self.speaker.say(text)

                command = play_command_callback(text)
                if (interrupt_check()
                    or command=='exit'):
                    self._logger.debug("douban fm break")
                    break
                operator = {
                    "p": self.playNextSong,
                    "s": self.playNextActionSong,
                    "r": self.playNextLikeSong,
                    "u": self.playNextUnLikeSong,
                    "b": self.playNextBanSong,
                    #"stop": self.stopSong,
                }
                if operator.has_key(command):
                    operator[command]()
                else:
                    continue

        self._logger.debug("douban fm over")


