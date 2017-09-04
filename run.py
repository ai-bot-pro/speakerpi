# -*- coding: utf-8-*-

import sys
import argparse
import logging
import signal

from lib.voice.baiduVoice import BaiduVoice
from plugin.fm.doubanFM import DoubanFM

interrupted = False

def signal_handler(signal, frame):
    global interrupted
    interrupted = True


def interrupt_callback():
    global interrupted
    return interrupted

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='doubanFM pi')
    parser.add_argument('--debug', action='store_true',
                        help='Show debug messages')
    args = parser.parse_args()

    logging.basicConfig(stream=sys.stdout)
    if args.debug:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

    baidu_voice = BaiduVoice.get_instance()
    douban_fm = DoubanFM.get_instance()

    baidu_voice.say("开始播放豆瓣电台")

    signal.signal(signal.SIGINT, signal_handler)

    douban_fm.start(interrupt_check=interrupt_callback,sleep_time=0.05)


