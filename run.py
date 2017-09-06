# -*- coding: utf-8-*-

import sys
import yaml
import argparse
import logging
import signal

from lib.voice.baiduVoice import BaiduVoice
from lib.mic import Mic,RawTextMic
import lib.appPath
import lib.util

from plugin.fm.doubanFM import DoubanFM

parser = argparse.ArgumentParser(description='doubanFM pi')
parser.add_argument('--debug', action='store_true',
                    help='Show debug messages')
parser.add_argument('--local', action='store_true',
                    help='Use text input instead of a real microphone')
args = parser.parse_args()

logging.basicConfig(stream=sys.stdout)
if args.debug:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

interrupted = False

def signal_handler(signal, frame):
    global interrupted
    interrupted = True

def interrupt_callback():
    global interrupted
    return interrupted

def run(robot_name="ROBOT"):
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
        self._logger.error("Can't open config file: '%s'", bootstrap_file)
        raise
       
    #语音唤醒实例
    try:
        passive_stt_engine = bootstrap_config['passive_stt_engine']
    except KeyError:
        stt_engine_tag = 'snowboy'
        logger.warning("passive_stt_engine not specified in profile, defaulting " + "to '%s'", passive_stt_engine)
    passive_stt_engine_class = lib.util.get_engine_by_tag(passive_stt_engine)

    #语音识别实例
    try:
        active_stt_engine = bootstrap_config['active_stt_engine']
    except KeyError:
        stt_engine_tag = 'baidu-ai-voice'
        logger.warning("active_stt_engine not specified in profile, defaulting " + "to '%s'", active_stt_engine)
    active_stt_engine_class = lib.util.get_engine_by_tag(active_stt_engine)

    #语音合成实例
    try:
        speak_engine = bootstrap_config['speak_engine']
    except KeyError:
        stt_engine_tag = 'baidu-ai-voice'
        logger.warning("speak_engine not specified in profile, defaulting " + "to '%s'", speak_engine)
    speak_engine_class = lib.util.get_engine_by_tag(speak_engine)
    
    #语音录入实例
    mic = Mic()
    
    #会话(指令)初始
    conversation = Conversation(robot_name, mic, 
            speak_engine_class, active_stt_engine_class, passive_stt_engine_class, bootstrap_config)

    #开始交互
    conversation.handleForever()


if __name__ == '__main__':

    baidu_voice = BaiduVoice.get_instance()
    douban_fm = DoubanFM.get_instance()

    baidu_voice.say("开始播放豆瓣电台")

    signal.signal(signal.SIGINT, signal_handler)

    douban_fm.start(interrupt_check=interrupt_callback,sleep_time=0.05)


