# -*- coding: utf-8-*-

import sys
import os
import yaml
import argparse
import logging
import signal

from lib.voice.baiduVoice import BaiduVoice
from lib.voice.snowboyVoice import SnowboyVoice
from lib.mic import Mic,RawTextMic
import lib.appPath
import lib.util

from plugin.fm.doubanFM import DoubanFM
import plugin.fm.doubanFM
from lib.conversation import Conversation

parser = argparse.ArgumentParser(description='doubanFM pi')
parser.add_argument('--debug', action='store_true',
                    help='Show debug messages')
args = parser.parse_args()

logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger("")
if args.debug:
    logger.setLevel(logging.DEBUG)


def run(robot_name="ROBOT"):
    global logger
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
    mic = Mic()
    
    #会话(指令)初始
    conversation = Conversation(robot_name, mic, 
            speak_engine_class.get_instance(), 
            active_stt_engine_class.get_instance(),
            passive_stt_engine_class.get_instance(),
            bootstrap_config)

    #开始交互
    conversation.handleForever()

def debugDoubanFm():
    baidu_voice = BaiduVoice.get_instance()
    text = "播放豆瓣电台"
    is_valid = plugin.fm.doubanFM.isValid(text)
    if is_valid is True:
        plugin.fm.doubanFM.handle(text,baidu_voice)

        

if __name__ == '__main__':

    #debugDoubanFm()
    run('xiaowu')



