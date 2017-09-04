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

import yaml

import lib.appPath
from baseFM import AbstractFM
from lib.voice.baiduVoice import BaiduVoice

class DoubanFM(AbstractFM):

    def is_available(cls):
        return (super(cls, cls).is_available() and
                diagnose.check_network_connection('www.douban.com'))

    def __init__(self, account_id, password, douban_id=None,
            cookie_file=os.path.join(lib.appPath.DATA_PATH, 'douban_cookie.txt'),
            cur_song_file=os.path.join(lib.appPath.DATA_PATH, 'douban_cur_song.txt')):
        super(self.__class__, self).__init__()
        self.ck = None
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
        self._mplay_process.wait()
        sid = self._getSidFromLocal()
        self.getSong(type='r',sid=sid)
        self.playSong()

    def playNextUnLikeSong(self):
        self._mplay_process.wait()
        sid = self._getSidFromLocal()
        self.getSong(type='u',sid=sid)
        self.playSong()

    def playNextBanSong(self):
        if self._mplay_process.pid is not None:
            self._mplay_process.kill()
        sid = self._getSidFromLocal()
        self.getSong(type='b',sid=sid)
        self.playSong()

    def playNextActionSong(self):
        if self._mplay_process.pid is not None:
            self._mplay_process.kill()
        sid = self._getSidFromLocal()
        self.getSong(type='p',sid=sid)
        self.playSong()

    def playNextSong(self):
        '''
        自然播放到下首歌
        '''
        sid = self._getSidFromLocal()
        type = 'p'
        if sid is None:
            type='n'
        self.getSong(type=type,sid=sid)
        self.playSong()
        
    def playSong(self):
        song = self._song
        if song is not None:
            try:
                albumtitle = song['albumtitle'].encode('UTF-8')
                url = song['url'].encode('UTF-8')
                title = song['title'].encode('UTF-8')
                artist = song['artist'].encode('UTF-8')
                region = song['singers'][0]['region'][0].encode('UTF-8')
                singer_info = "歌曲" + title + "来自专辑" + albumtitle + "由" + region +"歌手" + artist + "演唱"
                BaiduVoice.get_instance().say(singer_info)
                self.mplay(url)
            except IndexError,TypeError:
                self._logger.error("播放%s 失败",url)
                pass

    def start(self, command_callback=None,
              interrupt_check=lambda: False,
              sleep_time=0.03):
        
        self._logger.debug("douban fm start")
        while True:
            if interrupt_check():
                self._logger.debug("douban fm break")
                break
            self.playNextSong()
            if command_callback is not None:
                time.sleep(sleep_time)
                command = command_callback()
                operator = {
                    #"p": self.playNextSong,
                    "s": self.playNextActionSong,
                    "r": self.playNextLikeSong,
                    "u": self.playNextUnLikeSong,
                    "b": self.playNextBanSong,
                }
                operator[command]()

        self._logger.debug("douban fm over")
