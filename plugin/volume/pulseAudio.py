# -*- coding: utf-8-*-
import os,sys,re
import lib.appPath
from lib.baseClass import AbstractClass

TAG = 'pulseAudio'
CATE = 'volume'

def son_process_handle(speaker,get_text_callback):
    '''
    子进程处理逻辑
    speaker: voice实例(tts)
    get_text_callback: 获取文本指令回调函数
    '''
    print("<<<<<<< begin pulseAudio son process handle >>>>>>>")
    pass

def send_handle(text,in_fp,son_processor,speaker):
    '''
    发送指令给子进程处理(pipe,signal); 注意：如果不需要和子进程进行通信，直接可以在这个函数中处理
    text: 指令
    in_fp: pipe 输入端
    son_processor: 子进程(Process 实例)
    speaker: voice实例(tts)
    '''
    print("<<<<<<< begin pulseAudio send pipe handle >>>>>>>")
    res = False
    if re.search(u'大点', text) or re.search(u'大一点', text) or re.search(u'声音大', text):
        res = PulseAudio.turnUp()
    if re.search(u'小点', text) or re.search(u'小一点', text) or re.search(u'声音小', text):
        res = PulseAudio.turnDown()
    if re.search(u'静音', text):
        speaker.say(text.encode("UTF-8")+"操作后就不能听到我的声音了，请用打开声音指令")
        res = PulseAudio.off()
    if re.search(u'安静', text):
        speaker.say(text.encode("UTF-8")+"操作后就不能听到我的声音了，请用打开声音指令")
        res = PulseAudio.off()
    if re.search(u'打开声音', text):
        res = PulseAudio.on()
    if res is not False:
        print("%s is ok"%text.encode("UTF-8"))
        speaker.say(text.encode("UTF-8")+"操作好啦")

    in_fp.close()
    son_processor.join()
    pid_file = os.path.join(lib.appPath.DATA_PATH, CATE+"_"+__name__+'.pid');
    if os.path.exists(pid_file):
        os.remove(pid_file)

def isValid(text):
    valid_words = [
            u"声音大点",
            u"声音大一点",
            u"声音再大一点",
            u"声音在大一点",
            u"声音小点", 
            u"声音小一点", 
            u"声音再小一点",
            u"声音在小一点",
            u"静音",
            u"安静",
            u"打开声音",
            #u"声音放到最大",
        ]

    res = any(word in text for word in valid_words)
    return res

class PulseAudio(AbstractClass):
    def __init__(self):
        super(self.__class__, self).__init__()
        pass

    @classmethod
    def is_available(cls):
        '''
        u can use pactl pacmd for linux
        '''
        return (super(cls, cls).is_available() and
                lib.diagnose.check_executable('pulseaudio')
                and lib.diagnose.check_executable('amixer'))

    @classmethod
    def turnUp(cls):
        cur_volume_cmd = "amixer -D pulse sget Master | tail -n 1 |awk  -F'[\[\]\%]' '{print $2}'"
        cur_volume_percent = os.popen(cur_volume_cmd).readline()
        up_volume_percent = int(cur_volume_percent) + 5
        up_volume_cmd = "amixer -D pulse sset Master "+str(up_volume_percent)+"%"
        return os.system(up_volume_cmd)
        
    @classmethod
    def turnDown(cls):
        cur_volume_cmd = "amixer -D pulse sget Master | tail -n 1 |awk  -F'[\[\]\%]' '{print $2}'"
        cur_volume_percent = os.popen(cur_volume_cmd).readline()
        down_volume_percent = int(cur_volume_percent) - 5
        down_volume_cmd = "amixer -D pulse sset Master "+str(down_volume_percent)+"%"
        return os.system(down_volume_cmd)

    @classmethod
    def off(cls):
        cmd = "amixer -D pulse sset Master off" 
        return os.system(cmd)

    @classmethod
    def on(cls):
        cmd = "amixer -D pulse sset Master on" 
        return os.system(cmd)

    @classmethod
    def maxVolume(cls):
        cmd = "amixer -D pulse sset Master 100%" 
        return os.system(cmd)

